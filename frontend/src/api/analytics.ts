import api from "@/api/axios";

export const getTopItems = async (
  time_range: string,
  limit: number,
  itemType: string,
) => {
  const response = await api.get(`/analytics/top-items/${itemType}`, {
    params: { time_range, limit },
  });
  return response.data;
};

export const getRecentlyPlayed = async (limit: number) => {
  const response = await api.get("/analytics/recently-played", {
    params: { limit },
  });
  return response.data;
};

export const getUserPlaylists = async (limit: number, offset: number) => {
  const response = await api.get("/analytics/playlists", {
    params: { limit, offset },
  });
  return response.data;
};

export interface TopEntity {
  id: string;
  name: string;
  play_count: number;
  image_url?: string;
  artist_name?: string;
}

export interface OverviewResponse {
  window_days: number;
  total_tracks: number;
  total_hours: number;
  unique_artists: number;
  unique_tracks: number;
  top_artist: TopEntity | null;
  top_track: TopEntity | null;
}

export interface DailyPoint {
  date: string; // ISO date "YYYY-MM-DD"
  plays: number;
  minutes: number;
}

export interface DailyTrendResponse {
  days: number;
  points: DailyPoint[];
}

export interface GenreSlice {
  name: string;
  weight: number;
  artist_count: number;
}

export interface GenreDistributionResponse {
  slices: GenreSlice[];
  total_genres: number;
  based_on_artists: number;
}

export interface TodaySummaryResponse {
  total_tracks: number;
  listening_time: string;
  listening_time_ms: number;
}

export interface HourBucket {
  hour: number;
  count: number;
}

export interface HourlyVelocityResponse {
  hours: HourBucket[];
}

export interface HistoryItem {
  id: number;
  track_id: string;
  track_name: string;
  artist_id: string;
  artist_name: string;
  album_id: string;
  album_name: string;
  album_art_url?: string;
  duration_ms: number;
  played_at: string; // ISO datetime
}

export const getOverview = async (days = 30): Promise<OverviewResponse> => {
  const response = await api.get("/deep-analytics/overview", { params: { days } });
  return response.data;
};

export const getDailyTrend = async (days = 30): Promise<DailyTrendResponse> => {
  const response = await api.get("/deep-analytics/daily-trend", {
    params: { days },
  });
  return response.data;
};

export const getGenreDistribution = async (
  top_n = 5,
): Promise<GenreDistributionResponse> => {
  const response = await api.get("/deep-analytics/genre-distribution", {
    params: { top_n },
  });
  return response.data;
};

export const getTodaySummary = async (): Promise<TodaySummaryResponse> => {
  const response = await api.get("/deep-analytics/summary/today");
  return response.data;
};

export const getHourlyVelocity = async (): Promise<HourlyVelocityResponse> => {
  const response = await api.get("/deep-analytics/hourly-velocity");
  return response.data;
};

export interface HistoryResponse {
  items: HistoryItem[];
  total: number;
  page: number;
  limit: number;
}

export const getHistory = async (
  page: number,
  limit: number,
): Promise<HistoryResponse> => {
  const response = await api.get("/deep-analytics/history", {
    params: { page, limit },
  });
  return response.data;
};
