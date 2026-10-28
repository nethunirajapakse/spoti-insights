/**
 * Demo-mode implementations of every API call the app makes. Each function
 * returns the same shape as its real counterpart in `@/api/analytics`, so no
 * component or hook needs to know whether it is looking at real or sample data.
 */
import type {
  DailyTrendResponse,
  GenreDistributionResponse,
  HistoryResponse,
  HourlyVelocityResponse,
  OverviewResponse,
  TodaySummaryResponse,
} from "@/api/analytics";
import {
  DEMO_ARTISTS,
  DEMO_GENRES,
  DEMO_PLAYLISTS,
  DEMO_TRACKS,
  DEMO_USER,
  daysAgo,
  getPlays,
  playsSince,
  toDateKey,
  type DemoArtist,
  type DemoTrack,
} from "@/demo/demoData";

// A short delay keeps loading skeletons visible for a moment, like a real API.
const respond = <T>(value: T, ms = 180): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(value), ms));

const countBy = <T>(items: T[], key: (item: T) => string): Map<string, number> => {
  const counts = new Map<string, number>();
  for (const item of items) {
    const k = key(item);
    counts.set(k, (counts.get(k) ?? 0) + 1);
  }
  return counts;
};

const topKey = (counts: Map<string, number>): [string, number] | null => {
  let best: [string, number] | null = null;
  for (const entry of counts) {
    if (!best || entry[1] > best[1]) best = entry;
  }
  return best;
};

// --- Auth ------------------------------------------------------------------

export const demoCurrentUser = () => respond({ ...DEMO_USER }, 60);

// --- Deep analytics --------------------------------------------------------

export const demoOverview = (days: number): Promise<OverviewResponse> => {
  const plays = playsSince(daysAgo(days));
  const totalMs = plays.reduce((sum, p) => sum + p.track.durationMs, 0);

  const artistCounts = countBy(plays, (p) => p.track.artist.id);
  const trackCounts = countBy(plays, (p) => p.track.id);

  const topArtistEntry = topKey(artistCounts);
  const topTrackEntry = topKey(trackCounts);

  const topArtist = topArtistEntry
    ? DEMO_ARTISTS.find((a) => a.id === topArtistEntry[0])
    : undefined;
  const topTrack = topTrackEntry
    ? DEMO_TRACKS.find((t) => t.id === topTrackEntry[0])
    : undefined;

  return respond({
    window_days: days,
    total_tracks: plays.length,
    total_hours: Math.round((totalMs / 3_600_000) * 10) / 10,
    unique_artists: artistCounts.size,
    unique_tracks: trackCounts.size,
    top_artist:
      topArtist && topArtistEntry
        ? {
            id: topArtist.id,
            name: topArtist.name,
            play_count: topArtistEntry[1],
            image_url: topArtist.image,
          }
        : null,
    top_track:
      topTrack && topTrackEntry
        ? {
            id: topTrack.id,
            name: topTrack.name,
            artist_name: topTrack.artist.name,
            play_count: topTrackEntry[1],
            image_url: topTrack.art,
          }
        : null,
  });
};

export const demoDailyTrend = (days: number): Promise<DailyTrendResponse> => {
  const byDay = new Map<string, { plays: number; ms: number }>();
  for (const p of getPlays()) {
    const key = toDateKey(p.playedAt);
    const entry = byDay.get(key) ?? { plays: 0, ms: 0 };
    entry.plays += 1;
    entry.ms += p.track.durationMs;
    byDay.set(key, entry);
  }

  const today = new Date();
  const points = Array.from({ length: days }, (_, i) => {
    const date = new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate() - (days - 1 - i),
    );
    const key = toDateKey(date);
    const entry = byDay.get(key) ?? { plays: 0, ms: 0 };
    return { date: key, plays: entry.plays, minutes: Math.floor(entry.ms / 60_000) };
  });

  return respond({ days, points });
};

export const demoGenreDistribution = (): Promise<GenreDistributionResponse> =>
  respond({
    ...DEMO_GENRES,
    slices: DEMO_GENRES.slices.map((s) => ({ ...s })),
  });

export const demoTodaySummary = (): Promise<TodaySummaryResponse> => {
  const todayKey = toDateKey(new Date());
  const plays = getPlays().filter((p) => toDateKey(p.playedAt) === todayKey);
  const totalMs = plays.reduce((sum, p) => sum + p.track.durationMs, 0);
  const hours = Math.floor(totalMs / 3_600_000);
  const minutes = Math.floor((totalMs % 3_600_000) / 60_000);

  return respond({
    total_tracks: plays.length,
    listening_time: `${hours}h ${minutes}m`,
    listening_time_ms: totalMs,
  });
};

export const demoHourlyVelocity = (): Promise<HourlyVelocityResponse> => {
  const counts = new Array<number>(24).fill(0);
  for (const p of playsSince(daysAgo(1))) {
    counts[p.playedAt.getHours()] += 1;
  }
  return respond({ hours: counts.map((count, hour) => ({ hour, count })) });
};

export const demoHistory = (page: number, limit: number): Promise<HistoryResponse> => {
  const plays = getPlays();
  const start = (page - 1) * limit;

  return respond({
    items: plays.slice(start, start + limit).map((p) => ({
      id: p.id,
      track_id: p.track.id,
      track_name: p.track.name,
      artist_id: p.track.artist.id,
      artist_name: p.track.artist.name,
      album_id: p.track.albumId,
      album_name: p.track.albumName,
      album_art_url: p.track.art,
      duration_ms: p.track.durationMs,
      played_at: p.playedAt.toISOString(),
    })),
    total: plays.length,
    page,
    limit,
  });
};

// --- Spotify-shaped endpoints ---------------------------------------------

type TimeRange = "short_term" | "medium_term" | "long_term";

const RANGE_DAYS: Record<TimeRange, number> = {
  short_term: 10,
  medium_term: 30,
  long_term: 30,
};

// Long-term "all time" favourites shouldn't be identical to the last 30 days,
// so nudge each track's score by a stable per-track amount.
const rangeBias = (id: string, range: TimeRange): number => {
  if (range !== "long_term") return 0;
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) % 97;
  return h / 4;
};

const spotifyTrack = (t: DemoTrack) => ({
  id: t.id,
  name: t.name,
  artists: [{ id: t.artist.id, name: t.artist.name }],
  duration_ms: t.durationMs,
  album: {
    id: t.albumId,
    name: t.albumName,
    images: [{ url: t.art }, { url: t.art }, { url: t.art }],
  },
});

const spotifyArtist = (a: DemoArtist) => ({
  id: a.id,
  name: a.name,
  genres: a.genres,
  images: [{ url: a.image }, { url: a.image }, { url: a.image }],
});

export const demoTopItems = (timeRange: string, limit: number, itemType: string) => {
  const range = (timeRange in RANGE_DAYS ? timeRange : "medium_term") as TimeRange;
  const plays = playsSince(daysAgo(RANGE_DAYS[range]));

  if (itemType === "artists") {
    const counts = countBy(plays, (p) => p.track.artist.id);
    const items = [...DEMO_ARTISTS]
      .sort(
        (a, b) =>
          (counts.get(b.id) ?? 0) + rangeBias(b.id, range) -
          ((counts.get(a.id) ?? 0) + rangeBias(a.id, range)),
      )
      .slice(0, limit)
      .map(spotifyArtist);
    return respond({ items, total: items.length, limit, offset: 0 });
  }

  const counts = countBy(plays, (p) => p.track.id);
  const items = [...DEMO_TRACKS]
    .sort(
      (a, b) =>
        (counts.get(b.id) ?? 0) + rangeBias(b.id, range) -
        ((counts.get(a.id) ?? 0) + rangeBias(a.id, range)),
    )
    .slice(0, limit)
    .map(spotifyTrack);
  return respond({ items, total: items.length, limit, offset: 0 });
};

export const demoRecentlyPlayed = (limit: number) =>
  respond({
    items: getPlays()
      .slice(0, limit)
      .map((p) => ({
        track: spotifyTrack(p.track),
        played_at: p.playedAt.toISOString(),
      })),
  });

export const demoPlaylists = (limit: number, offset: number) => {
  const items = DEMO_PLAYLISTS.slice(offset, offset + limit);
  const hasMore = offset + limit < DEMO_PLAYLISTS.length;
  return respond({
    items,
    total: DEMO_PLAYLISTS.length,
    limit,
    offset,
    next: hasMore ? "demo-next" : null,
  });
};
