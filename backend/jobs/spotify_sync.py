import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.database.connection import SessionLocal
from backend.models.user import User
from backend.models.analytics import ListeningHistory, SyncState
from backend.services import auth_service
from backend.services.spotify_api_service import get_recently_played_tracks

logger = logging.getLogger(__name__)

# Postgres advisory lock key — arbitrary but stable. Prevents multiple workers
# from running run_sync_all() concurrently when deployed with --workers > 1.
_SYNC_LOCK_KEY = 0x53504F54  # "SPOT" in hex


async def sync_user(user: User, db: Session) -> None:
    """Sync one user's recently played tracks into listening_history."""
    try:
        # Get a fresh access token via the existing service.
        tokens = await auth_service.refresh_user_spotify_access_token(
            db, user.spotify_id
        )
        access_token = tokens["access_token"]

        # Fetch the user's recent plays. Spotify caps at 50; the unique
        # constraint on (user_id, played_at) handles dedupe on insert.
        data = await get_recently_played_tracks(access_token, limit=50)
        items = data.get("items", [])
        if not items:
            return

        # Build all rows and do a single batched upsert
        rows = []
        for item in items:
            track = item["track"]
            played_at = datetime.fromisoformat(
                item["played_at"].replace("Z", "+00:00")
            )
            images = track["album"].get("images") or []
            rows.append({
                "user_id":       user.spotify_id,
                "track_id":      track["id"],
                "track_name":    track["name"],
                "artist_id":     track["artists"][0]["id"],
                "artist_name":   track["artists"][0]["name"],
                "album_id":      track["album"]["id"],
                "album_name":    track["album"]["name"],
                "album_art_url": images[0]["url"] if images else None,
                "duration_ms":   track["duration_ms"],
                "played_at":     played_at,
            })

        stmt = (
            insert(ListeningHistory)
            .values(rows)
            .on_conflict_do_nothing(constraint="uq_user_played_at")
        )
        db.execute(stmt)

        # Update last-sync timestamp (for observability only — no cursor)
        sync = (
            db.query(SyncState)
            .filter(SyncState.user_id == user.spotify_id)
            .first()
        )
        now = datetime.now(timezone.utc)
        latest_played_at = datetime.fromisoformat(
            items[0]["played_at"].replace("Z", "+00:00")
        )
        if sync:
            sync.last_played_at = latest_played_at
            sync.last_synced_at = now
        else:
            db.add(SyncState(
                user_id=user.spotify_id,
                last_played_at=latest_played_at,
                last_synced_at=now,
            ))

        db.commit()
        logger.info("Sync cycle complete for %s (Spotify returned %d items; new rows inserted by upsert)",
                user.spotify_id, len(items))

    except Exception as exc:
        db.rollback()
        logger.exception("Sync failed for %s: %s", user.spotify_id, exc)


async def run_sync_all() -> None:
    """
    Sync every user. Wrapped in a Postgres advisory lock so that if the app
    is deployed with multiple workers, only one runs this at a time.
    """
    db = SessionLocal()
    try:
        # Try to grab the advisory lock; bail out cleanly if another worker holds it.
        got_lock = db.execute(
            text("SELECT pg_try_advisory_lock(:key)"),
            {"key": _SYNC_LOCK_KEY},
        ).scalar()
        if not got_lock:
            logger.debug("Another worker holds the sync lock; skipping this run.")
            return

        try:
            users = db.query(User).all()
            for user in users:
                await sync_user(user, db)
        finally:
            db.execute(
                text("SELECT pg_advisory_unlock(:key)"),
                {"key": _SYNC_LOCK_KEY},
            )
            db.commit()
    finally:
        db.close()


def start_scheduler() -> AsyncIOScheduler:
    """
    Start the async scheduler on the current (FastAPI) event loop.
    Must be called from within a running event loop — i.e. inside lifespan().
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_sync_all,
        trigger="interval",
        minutes=15,
        next_run_time=datetime.now(timezone.utc),
        max_instances=1,           # never overlap if a run is slow
        coalesce=True,             # collapse missed runs into one
    )
    scheduler.start()
    logger.info("Spotify sync scheduler started")
    return scheduler
