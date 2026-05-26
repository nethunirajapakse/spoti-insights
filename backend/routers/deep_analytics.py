from datetime import date, datetime, time, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, extract
from sqlalchemy.orm import Session
from backend.core.dependencies import get_current_user
from backend.database.connection import get_db
from backend.models.analytics import ListeningHistory
from backend.schemas.analytics import (
    HistoryResponse,
    HourlyVelocityResponse,
    TodaySummaryResponse,
)

router = APIRouter(prefix="/deep-analytics", tags=["Deep Analytics"])

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[object, Depends(get_current_user)]  # tighten to your User type if you have it


@router.get("/history", response_model=HistoryResponse)
def get_history(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
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
    # Index-friendly: range filter on played_at, no cast() wrapping the column.
    today_start = datetime.combine(date.today(), time.min, tzinfo=timezone.utc)
    tomorrow_start = today_start + timedelta(days=1)

    # Aggregate in SQL — one round trip, no Python summing.
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
    # 24-hour window using a Python-side cutoff — same result, portable across DBs.
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

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

    return {"hours": [{"hour": int(r.hour), "count": int(r.count)} for r in rows]}
