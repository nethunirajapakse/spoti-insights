from datetime import date, datetime, time, timedelta, UTC
from typing import Annotated
from collections import Counter
import logging

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import func, extract, distinct, cast, Date
from sqlalchemy.orm import Session

from backend.core.dependencies import get_current_user
from backend.database.connection import get_db
from backend.models.user import User
from backend.models.analytics import ListeningHistory
from backend.schemas.analytics import (
    HistoryResponse,
    HourlyVelocityResponse,
    TodaySummaryResponse,
    OverviewResponse,
    DailyTrendResponse,
    GenreDistributionResponse,
    TopEntity,
    DailyPoint,
    GenreSlice,
)

from backend.routers.analytics import get_spotify_access_token_for_authenticated_user
from backend.services import spotify_api_service
from backend.services.spotify_api_service import SpotifyTopItemType, SpotifyTimeRange

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/deep-analytics", tags=["Deep Analytics"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
SpotifyAccessToken = Annotated[str, Depends(get_spotify_access_token_for_authenticated_user)]

PageQuery = Annotated[int, Query(ge=1)]
HistoryLimitQuery = Annotated[int, Query(ge=1, le=100)]
WindowDaysQuery = Annotated[int, Query(ge=1, le=365)]

# Hard upper bound enforced on the server, independent of any query value.
# Even if a request smuggles past validation, we never loop more than this.
MAX_TREND_DAYS = 365


# ============================================================
# EXISTING — unchanged
# ============================================================
@router.get("/history", response_model=HistoryResponse)
def get_history(
    user: CurrentUser,
    db: DbSession,
    page: PageQuery = 1,
    limit: HistoryLimitQuery = 20,
):
    offset = (page - 1) * limit
    items = (
        db.query(ListeningHistory)
        .filter(ListeningHistory.user_id == user.spotify_id)
        .order_by(ListeningHistory.played_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    total = (
        db.query(func.count(ListeningHistory.id))
        .filter(ListeningHistory.user_id == user.spotify_id)
        .scalar()
    ) or 0
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.get("/summary/today", response_model=TodaySummaryResponse)
def get_today_summary(user: CurrentUser, db: DbSession):
    today_start = datetime.combine(date.today(), time.min, tzinfo=UTC)
    tomorrow_start = today_start + timedelta(days=1)

    result = (
        db.query(
            func.count(ListeningHistory.id).label("count"),
            func.coalesce(func.sum(ListeningHistory.duration_ms), 0).label("total_ms"),
        )
        .filter(
            ListeningHistory.user_id == user.spotify_id,
            ListeningHistory.played_at >= today_start,
            ListeningHistory.played_at < tomorrow_start,
        )
        .one()
    )

    total_ms = int(result.total_ms or 0)
    hours, rem = divmod(total_ms // 1000, 3600)
    minutes = rem // 60

    return {
        "total_tracks": int(result.count or 0),
        "listening_time": f"{hours}h {minutes}m",
        "listening_time_ms": total_ms,
    }


@router.get("/hourly-velocity", response_model=HourlyVelocityResponse)
def get_hourly_velocity(user: CurrentUser, db: DbSession):
    """
    Hour-of-day distribution over the last 24h. Returns 24 buckets always —
    hours with zero plays are filled in so the frontend can render a clean
    24-bar histogram without index gymnastics.
    """
    cutoff = datetime.now(UTC) - timedelta(hours=24)
    rows = (
        db.query(
            extract("hour", ListeningHistory.played_at).label("hour"),
            func.count().label("count"),
        )
        .filter(
            ListeningHistory.user_id == user.spotify_id,
            ListeningHistory.played_at >= cutoff,
        )
        .group_by("hour")
        .order_by("hour")
        .all()
    )

    counts_by_hour = {int(r.hour): int(r.count) for r in rows}
    full = [{"hour": h, "count": counts_by_hour.get(h, 0)} for h in range(24)]
    return {"hours": full}


# ============================================================
# Dashboard endpoints
# ============================================================
async def _fetch_artist_image(access_token: str, artist_id: str) -> str | None:
    """
    Fetches a single artist's image. Returns None on any failure — image
    is bonus data, the stat card should still render without it.
    """
    try:
        artist_data = await spotify_api_service._make_spotify_request(
            access_token, "GET", f"/artists/{artist_id}"
        )
        images = artist_data.get("images") or []
        for img in images:
            if img.get("height") == 320:
                return img.get("url")
        return images[0].get("url") if images else None
    except Exception:
        logger.warning("Failed to fetch image for artist %s", artist_id, exc_info=True)
        return None


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    user: CurrentUser,
    db: DbSession,
    access_token: SpotifyAccessToken,
    days: WindowDaysQuery = 30,
):
    """
    Stat row data: totals and top entity (artist + track) by play count
    over the last N days. Top artist is enriched with image URL via one
    extra Spotify call — graceful degradation if Spotify is slow/down.
    """
    # Defensive re-clamp: Pydantic already validates the range, but Sonar
    # treats raw query values as tainted. Recomputing into a local guards
    # against any future change that loosens the validator.
    safe_days = max(1, min(int(days), MAX_TREND_DAYS))

    cutoff = datetime.now(UTC) - timedelta(days=safe_days)
    user_filter = ListeningHistory.user_id == user.spotify_id
    window_filter = ListeningHistory.played_at >= cutoff

    totals = (
        db.query(
            func.count(ListeningHistory.id).label("total_tracks"),
            func.coalesce(func.sum(ListeningHistory.duration_ms), 0).label("total_ms"),
            func.count(distinct(ListeningHistory.artist_id)).label("unique_artists"),
            func.count(distinct(ListeningHistory.track_id)).label("unique_tracks"),
        )
        .filter(user_filter, window_filter)
        .one()
    )

    total_ms = int(totals.total_ms or 0)
    total_hours = round(total_ms / 3_600_000, 1)

    top_artist_row = (
        db.query(
            ListeningHistory.artist_id,
            ListeningHistory.artist_name,
            func.count().label("plays"),
        )
        .filter(user_filter, window_filter)
        .group_by(ListeningHistory.artist_id, ListeningHistory.artist_name)
        .order_by(func.count().desc())
        .first()
    )

    top_track_row = (
        db.query(
            ListeningHistory.track_id,
            ListeningHistory.track_name,
            ListeningHistory.artist_name,
            ListeningHistory.album_art_url,
            func.count().label("plays"),
        )
        .filter(user_filter, window_filter)
        .group_by(
            ListeningHistory.track_id,
            ListeningHistory.track_name,
            ListeningHistory.artist_name,
            ListeningHistory.album_art_url,
        )
        .order_by(func.count().desc())
        .first()
    )

    top_artist = None
    if top_artist_row:
        image_url = await _fetch_artist_image(access_token, top_artist_row.artist_id)
        top_artist = TopEntity(
            id=top_artist_row.artist_id,
            name=top_artist_row.artist_name,
            play_count=int(top_artist_row.plays),
            image_url=image_url,
        )

    top_track = None
    if top_track_row:
        top_track = TopEntity(
            id=top_track_row.track_id,
            name=top_track_row.track_name,
            artist_name=top_track_row.artist_name,
            image_url=top_track_row.album_art_url,
            play_count=int(top_track_row.plays),
        )

    return OverviewResponse(
        window_days=safe_days,
        total_tracks=int(totals.total_tracks or 0),
        total_hours=total_hours,
        unique_artists=int(totals.unique_artists or 0),
        unique_tracks=int(totals.unique_tracks or 0),
        top_artist=top_artist,
        top_track=top_track,
    )


@router.get("/daily-trend", response_model=DailyTrendResponse)
def get_daily_trend(
    user: CurrentUser,
    db: DbSession,
    days: WindowDaysQuery = 30,
):
    """
    Per-day play count and listening minutes for the last N days.
    Days with zero plays are filled in so the line chart renders smoothly.
    """
    # Defensive re-clamp before using `days` as a loop bound. Pydantic already
    # enforces 1 <= days <= 365 via WindowDaysQuery, but Sonar's taint analysis
    # flags any user-controlled value reaching `range()`. Re-binding into a
    # local int with explicit min/max satisfies the analyzer and guards against
    # any future change to the query validator.
    safe_days = max(1, min(int(days), MAX_TREND_DAYS))

    today_utc = datetime.now(UTC).date()
    start_date = today_utc - timedelta(days=safe_days - 1)
    cutoff = datetime.combine(start_date, time.min, tzinfo=UTC)

    day_col = cast(ListeningHistory.played_at, Date).label("day")

    rows = (
        db.query(
            day_col,
            func.count().label("plays"),
            func.coalesce(func.sum(ListeningHistory.duration_ms), 0).label("ms"),
        )
        .filter(
            ListeningHistory.user_id == user.spotify_id,
            ListeningHistory.played_at >= cutoff,
        )
        .group_by(day_col)
        .order_by(day_col)
        .all()
    )

    by_day = {r.day: (int(r.plays), int(r.ms or 0)) for r in rows}

    points = []
    for offset in range(safe_days):
        d = start_date + timedelta(days=offset)
        plays, ms = by_day.get(d, (0, 0))
        points.append(DailyPoint(date=d, plays=plays, minutes=ms // 60_000))

    return DailyTrendResponse(days=safe_days, points=points)


@router.get("/genre-distribution", response_model=GenreDistributionResponse)
async def get_genre_distribution(
    user: CurrentUser,
    access_token: SpotifyAccessToken,
    top_n: Annotated[int, Query(ge=2, le=10)] = 5,
):
    """
    Aggregates genres across the user's top artists (medium_term, ~6 months).
    Spotify only tags genres at the artist level, so this is the cleanest
    proxy for the user's genre taste.
    """
    try:
        top_artists = await spotify_api_service.get_user_top_items(
            access_token,
            SpotifyTopItemType.ARTISTS,
            SpotifyTimeRange.MEDIUM_TERM,
            limit=50,
        )
    except spotify_api_service.SpotifyAPIError as e:
        raise HTTPException(
            status_code=e.status_code or status.HTTP_502_BAD_GATEWAY,
            detail=e.message,
        )

    artists = top_artists.get("items", [])
    if not artists:
        return GenreDistributionResponse(
            slices=[], total_genres=0, based_on_artists=0
        )

    genre_counter: Counter[str] = Counter()
    for artist in artists:
        for genre in artist.get("genres", []) or []:
            genre_counter[genre] += 1

    if not genre_counter:
        return GenreDistributionResponse(
            slices=[], total_genres=0, based_on_artists=len(artists)
        )

    total_tags = sum(genre_counter.values())
    most_common = genre_counter.most_common(top_n)

    slices = [
        GenreSlice(
            name=name.title(),
            weight=round(count / total_tags * 100),
            artist_count=count,
        )
        for name, count in most_common
    ]

    if len(genre_counter) > top_n:
        other_count = total_tags - sum(c for _, c in most_common)
        slices.append(
            GenreSlice(
                name="Other",
                weight=round(other_count / total_tags * 100),
                artist_count=other_count,
            )
        )

    return GenreDistributionResponse(
        slices=slices,
        total_genres=len(genre_counter),
        based_on_artists=len(artists),
    )
