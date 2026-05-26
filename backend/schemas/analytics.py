from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ListeningHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    track_id: str
    track_name: str
    artist_id: str
    artist_name: str
    album_id: str
    album_name: str
    album_art_url: Optional[str] = None
    duration_ms: int
    played_at: datetime


class HistoryResponse(BaseModel):
    items: list[ListeningHistoryItem]
    total: int
    page: int
    limit: int


class TodaySummaryResponse(BaseModel):
    total_tracks: int
    listening_time: str
    listening_time_ms: int


class HourBucket(BaseModel):
    hour: int
    count: int


class HourlyVelocityResponse(BaseModel):
    hours: list[HourBucket]
