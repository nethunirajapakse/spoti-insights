import logging
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler  # sync scheduler
from sqlalchemy.dialects.postgresql import insert
from backend.database.connection import SessionLocal
from backend.models.user import User
from backend.models.analytics import ListeningHistory, SyncState
from backend.services.spotify_api_service import get_recently_played_tracks

logger = logging.getLogger(__name__)


def sync_user(user: User, db):
    try:
        # Your existing token refresh logic here
        from backend.core.dependencies import get_valid_access_token
        access_token = get_valid_access_token(user, db)

        # 1. Get cursor
        sync = db.query(SyncState).filter(SyncState.user_id == user.spotify_id).first()
        params = {"limit": 50}
        if sync and sync.last_played_at:
            params["after"] = int(sync.last_played_at.timestamp() * 1000)

        # 2. Fetch from Spotify
        import asyncio
        data = asyncio.run(get_recently_played_tracks(access_token, limit=50))
        items = data.get("items", [])
        if not items:
            return

        # 3. Upsert into listening_history
        for item in items:
            track = item["track"]
            played_at = datetime.fromisoformat(
                item["played_at"].replace("Z", "+00:00")
            )
            stmt = insert(ListeningHistory).values(
                user_id       = user.spotify_id,
                track_id      = track["id"],
                track_name    = track["name"],
                artist_id     = track["artists"][0]["id"],
                artist_name   = track["artists"][0]["name"],
                album_id      = track["album"]["id"],
                album_name    = track["album"]["name"],
                album_art_url = track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                duration_ms   = track["duration_ms"],
                played_at     = played_at,
            ).on_conflict_do_nothing(constraint="uq_user_played_at")
            db.execute(stmt)

        # 4. Update cursor
        latest_played_at = datetime.fromisoformat(
            items[0]["played_at"].replace("Z", "+00:00")
        )
        if sync:
            sync.last_played_at = latest_played_at
            sync.last_synced_at = datetime.now(timezone.utc)
        else:
            db.add(SyncState(
                user_id        = user.spotify_id,
                last_played_at = latest_played_at,
                last_synced_at = datetime.now(timezone.utc),
            ))

        db.commit()
        logger.info(f"Synced {len(items)} tracks for {user.spotify_id}")

    except Exception as e:
        db.rollback()
        logger.error(f"Sync failed for {user.spotify_id}: {e}")


def run_sync_all():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            sync_user(user, db)
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_sync_all,
        trigger="interval",
        minutes=15,
        next_run_time=datetime.now(timezone.utc),
    )
    scheduler.start()
    logger.info("Spotify sync scheduler started")
    return scheduler
