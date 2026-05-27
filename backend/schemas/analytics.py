from datetime import datetime, date
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


class TopEntity(BaseModel):
    """A top artist or track derived from listening history play counts."""
    id: str
    name: str
    play_count: int
    image_url: Optional[str] = None
    # For tracks only
    artist_name: Optional[str] = None


class OverviewResponse(BaseModel):
    """30-day rollup powering the Dashboard stat row."""
    window_days: int
    total_tracks: int          # total plays in window (rows)
    total_hours: float         # sum(duration_ms) / 3_600_000, rounded to 1 dp
    unique_artists: int
    unique_tracks: int
    top_artist: Optional[TopEntity] = None
    top_track: Optional[TopEntity] = None


class DailyPoint(BaseModel):
    """One day in the trend line."""
    date: date
    plays: int
    minutes: int


class DailyTrendResponse(BaseModel):
    days: int
    points: list[DailyPoint]


class GenreSlice(BaseModel):
    name: str
    weight: int           # 0-100 (percent rounded)
    artist_count: int


class GenreDistributionResponse(BaseModel):
    slices: list[GenreSlice]      # ordered desc by weight; capped to top N + 'Other'
    total_genres: int             # total distinct genres seen across top artists
    based_on_artists: int         # how many top artists were aggregated
