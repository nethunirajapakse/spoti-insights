from sqlalchemy import Column, Integer, String, TIMESTAMP, UniqueConstraint, Index
from backend.database.connection import Base

class ListeningHistory(Base):
    __tablename__ = "listening_history"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(String, nullable=False)
    track_id      = Column(String, nullable=False)
    track_name    = Column(String, nullable=False)
    artist_id     = Column(String, nullable=False)
    artist_name   = Column(String, nullable=False)
    album_id      = Column(String, nullable=False)
    album_name    = Column(String, nullable=False)
    album_art_url = Column(String)
    duration_ms   = Column(Integer, nullable=False)
    played_at     = Column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "played_at", name="uq_user_played_at"),
        Index("ix_user_played_at", "user_id", "played_at"),
    )


class SyncState(Base):
    __tablename__ = "sync_state"

    user_id        = Column(String, primary_key=True)
    last_played_at = Column(TIMESTAMP(timezone=True))
    last_synced_at = Column(TIMESTAMP(timezone=True))
