from sqlalchemy.orm import Session
from sqlalchemy import func, extract, text, cast, Date
from datetime import date, timedelta
from backend.models.analytics import ListeningHistory

@router.get("/history")
def get_history(
    page: int = 1,
    limit: int = 20,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * limit
    items = (
        db.query(ListeningHistory)
        .filter(ListeningHistory.user_id == user.spotify_id)
        .order_by(ListeningHistory.played_at.desc())
        .limit(limit).offset(offset)
        .all()
    )
    total = db.query(func.count(ListeningHistory.id))\
              .filter(ListeningHistory.user_id == user.spotify_id)\
              .scalar()
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.get("/summary/today")
def get_today_summary(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(ListeningHistory.duration_ms)
        .filter(
            ListeningHistory.user_id == user.spotify_id,
            cast(ListeningHistory.played_at, Date) == date.today()
        )
        .all()
    )
    total_ms = sum(r.duration_ms for r in rows)
    hours, rem = divmod(total_ms // 1000, 3600)
    minutes = rem // 60
    return {
        "total_tracks": len(rows),
        "listening_time": f"{hours}h {minutes}m",
        "listening_time_ms": total_ms,
    }


@router.get("/hourly-velocity")
def get_hourly_velocity(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(
            extract("hour", ListeningHistory.played_at).label("hour"),
            func.count().label("count")
        )
        .filter(
            ListeningHistory.user_id == user.spotify_id,
            ListeningHistory.played_at >= func.now() - text("interval '24 hours'")
        )
        .group_by("hour")
        .order_by("hour")
        .all()
    )
    return {"hours": [{"hour": int(r.hour), "count": r.count} for r in rows]}
