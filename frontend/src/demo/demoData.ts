/**
 * Sample dataset behind demo mode.
 *
 * Everything the dashboard shows (history, daily trend, hourly velocity, top
 * tracks, overview totals) is derived from ONE generated list of plays, so the
 * numbers agree with each other the way they do for a real account.
 *
 * The artists and tracks are invented. Generation is seeded, so the shape is
 * the same on every load, but dates are relative to "now" so the dashboard
 * always looks current.
 */

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

const DAY_MS = 86_400_000;
const SEED = 7_331_001;

const mulberry32 = (seed: number) => {
  let a = seed;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};

const hashString = (s: string): number => {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
};

const slug = (s: string) =>
  s
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");

const pad = (n: number) => String(n).padStart(2, "0");

/** Local calendar date as YYYY-MM-DD. */
export const toDateKey = (d: Date) =>
  `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

const pickWeighted = (weights: number[], rand: () => number): number => {
  const total = weights.reduce((a, b) => a + b, 0);
  let r = rand() * total;
  for (let i = 0; i < weights.length; i++) {
    r -= weights[i];
    if (r <= 0) return i;
  }
  return weights.length - 1;
};

/**
 * Generates a square gradient "album cover" as an inline SVG data URI, so the
 * demo needs no image hosting and can't show a broken image.
 */
export const coverArt = (seed: string): string => {
  const h = hashString(seed);
  const hue1 = h % 360;
  const hue2 = (hue1 + 40 + ((h >>> 9) % 80)) % 360;
  const variant = (h >>> 5) % 3;

  let shape: string;
  if (variant === 0) {
    shape = `<circle cx="42" cy="22" r="14" fill="hsl(${hue2},70%,68%)" fill-opacity=".55"/>`;
  } else if (variant === 1) {
    shape = `<rect x="10" y="38" width="44" height="6" rx="3" fill="hsl(${hue2},70%,70%)" fill-opacity=".5"/><rect x="10" y="48" width="28" height="6" rx="3" fill="hsl(${hue2},70%,70%)" fill-opacity=".35"/>`;
  } else {
    shape = `<polygon points="0,64 64,18 64,64" fill="hsl(${hue2},70%,66%)" fill-opacity=".4"/>`;
  }

  const svg =
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">` +
    `<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">` +
    `<stop offset="0" stop-color="hsl(${hue1},60%,38%)"/>` +
    `<stop offset="1" stop-color="hsl(${hue2},65%,20%)"/>` +
    `</linearGradient></defs>` +
    `<rect width="64" height="64" fill="url(#g)"/>${shape}</svg>`;

  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
};

// ---------------------------------------------------------------------------
// Catalogue (invented artists and tracks)
// ---------------------------------------------------------------------------

type TrackSpec = [name: string, album: string, seconds: number, weight: number];

interface ArtistSpec {
  name: string;
  weight: number;
  genres: string[];
  tracks: TrackSpec[];
}

const ARTIST_SPECS: ArtistSpec[] = [
  {
    name: "Neon Harbor",
    weight: 20,
    genres: ["synthwave", "electropop"],
    tracks: [
      ["Afterglow Boulevard", "Night Transit", 214, 5],
      ["Chrome Hearts", "Night Transit", 198, 3],
      ["Static Skyline", "Night Transit", 231, 2],
      ["Pacific Drive", "Glass Coast", 247, 2],
    ],
  },
  {
    name: "Paper Lanterns",
    weight: 16,
    genres: ["indie pop", "dream pop"],
    tracks: [
      ["Small Hours", "Lantern Season", 203, 5],
      ["Porch Light", "Lantern Season", 187, 3],
      ["Honey in March", "Slow Bloom", 221, 2],
      ["Paper Moons", "Slow Bloom", 196, 2],
    ],
  },
  {
    name: "Velvet Static",
    weight: 13,
    genres: ["alt rock", "indie rock"],
    tracks: [
      ["Wire and Wishbone", "Low Voltage Hymns", 242, 4],
      ["Rust Belt Lullaby", "Low Voltage Hymns", 256, 3],
      ["Hum of the Highway", "Dead Air", 209, 2],
    ],
  },
  {
    name: "Luma Park",
    weight: 12,
    genres: ["lo-fi beats", "chillhop"],
    tracks: [
      ["Rainy Window Study", "Tape Hiss Tapes", 142, 4],
      ["Cold Brew Morning", "Tape Hiss Tapes", 156, 3],
      ["Bus Stop Loop", "Late Bloomers", 131, 3],
    ],
  },
  {
    name: "Orchid Season",
    weight: 9,
    genres: ["dream pop", "shoegaze"],
    tracks: [
      ["Soft Focus", "Greenhouse", 268, 3],
      ["Violet Hours", "Greenhouse", 279, 2],
      ["Overgrown", "Greenhouse", 251, 1],
    ],
  },
  {
    name: "Midnight Cartography",
    weight: 8,
    genres: ["electronic", "ambient"],
    tracks: [
      ["Mapping the Quiet", "Longitudes", 305, 2],
      ["Signal Bloom", "Longitudes", 287, 2],
      ["Dusk Protocol", "Longitudes", 262, 1],
    ],
  },
  {
    name: "Sable and Sound",
    weight: 7,
    genres: ["r&b", "neo soul"],
    tracks: [
      ["Velvet Hours", "Slow Burn", 233, 3],
      ["Say It Soft", "Slow Burn", 219, 2],
    ],
  },
  {
    name: "Glasshouse Choir",
    weight: 6,
    genres: ["indie folk", "chamber pop"],
    tracks: [
      ["Winter Orchard", "Evergreen Letters", 196, 2],
      ["Letters Home", "Evergreen Letters", 224, 2],
    ],
  },
  {
    name: "Tidal Mouth",
    weight: 5,
    genres: ["post-punk", "art rock"],
    tracks: [
      ["Salt Line", "Undertow", 187, 2],
      ["Concrete Garden", "Undertow", 203, 1],
    ],
  },
  {
    name: "Quiet Engines",
    weight: 4,
    genres: ["ambient", "downtempo"],
    tracks: [
      ["Idle Hours", "Hush Machines", 318, 2],
      ["Turbine Lullaby", "Hush Machines", 292, 1],
    ],
  },
];

export interface DemoArtist {
  id: string;
  name: string;
  genres: string[];
  image: string;
}

export interface DemoTrack {
  id: string;
  name: string;
  artist: DemoArtist;
  albumId: string;
  albumName: string;
  durationMs: number;
  art: string;
  weight: number;
}

const ARTISTS: DemoArtist[] = ARTIST_SPECS.map((a) => ({
  id: `demo-artist-${slug(a.name)}`,
  name: a.name,
  genres: a.genres,
  image: coverArt(`artist:${a.name}`),
}));

const TRACKS: DemoTrack[] = ARTIST_SPECS.flatMap((spec, artistIdx) =>
  spec.tracks.map(([name, album, seconds, weight]) => ({
    id: `demo-track-${slug(name)}`,
    name,
    artist: ARTISTS[artistIdx],
    albumId: `demo-album-${slug(album)}`,
    albumName: album,
    durationMs: seconds * 1000,
    art: coverArt(`album:${album}`),
    weight: spec.weight * weight,
  })),
);

const TRACK_WEIGHTS = TRACKS.map((t) => t.weight);

// ---------------------------------------------------------------------------
// Play generation
// ---------------------------------------------------------------------------

export interface DemoPlay {
  id: number;
  track: DemoTrack;
  playedAt: Date;
}

// Listening intensity by local hour of day (index = hour): a morning commute
// bump, a lunchtime bump, and a long evening peak.
const HOUR_WEIGHTS = [
  1, 0.5, 0.3, 0.2, 0.2, 0.4, 1.2, 3, 4.5, 3.2, 2.4, 2.2, 3, 3.4, 2.6, 2.2,
  2.4, 3, 3.4, 3.6, 4.2, 4.6, 3.6, 2.2,
];

const WINDOW_DAYS = 30;

let playsCache: DemoPlay[] | null = null;

const buildPlays = (): DemoPlay[] => {
  const rand = mulberry32(SEED);
  const now = new Date();
  const raw: { playedAt: Date; track: DemoTrack }[] = [];

  for (let d = WINDOW_DAYS - 1; d >= 0; d--) {
    const day = new Date(now.getFullYear(), now.getMonth(), now.getDate() - d);
    const isWeekend = day.getDay() === 0 || day.getDay() === 6;
    let count = Math.round((isWeekend ? 28 : 22) * (0.55 + rand() * 0.8));

    // Today is only partly over; scale it down so the "today" card looks
    // plausible at any hour instead of showing future plays.
    const isToday = d === 0;
    const maxHour = isToday ? now.getHours() : 23;
    if (isToday) {
      const progress = (now.getHours() + 1) / 24;
      count = Math.max(4, Math.round(count * (0.3 + 0.7 * progress)));
    }

    const hourWeights = HOUR_WEIGHTS.map((w, h) => (h <= maxHour ? w : 0));

    for (let i = 0; i < count; i++) {
      const hour = pickWeighted(hourWeights, rand);
      const minute = Math.floor(rand() * 60);
      const second = Math.floor(rand() * 60);
      const track = TRACKS[pickWeighted(TRACK_WEIGHTS, rand)];

      let playedAt = new Date(
        day.getFullYear(),
        day.getMonth(),
        day.getDate(),
        hour,
        minute,
        second,
      );
      if (playedAt > now) {
        playedAt = new Date(now.getTime() - rand() * 30 * 60_000);
      }
      raw.push({ playedAt, track });
    }
  }

  // A person can only listen to one song at a time: walk the plays oldest to
  // newest and push any that would overlap the previous track back to just
  // after it ends. Plays pushed past "now" are dropped.
  raw.sort((a, b) => a.playedAt.getTime() - b.playedAt.getTime());
  const sequential: typeof raw = [];
  let previousEnd = 0;
  for (const play of raw) {
    let start = play.playedAt.getTime();
    if (start < previousEnd) {
      start = previousEnd + Math.floor(rand() * 90_000);
    }
    if (start > now.getTime()) continue;
    previousEnd = start + play.track.durationMs;
    sequential.push({ ...play, playedAt: new Date(start) });
  }

  sequential.reverse();
  return sequential.map((p, i) => ({ id: sequential.length - i, ...p }));
};

/** All demo plays, newest first. Generated once per page load. */
export const getPlays = (): DemoPlay[] => {
  playsCache ??= buildPlays();
  return playsCache;
};

export const playsSince = (cutoff: Date): DemoPlay[] =>
  getPlays().filter((p) => p.playedAt >= cutoff);

export const daysAgo = (days: number): Date =>
  new Date(Date.now() - days * DAY_MS);

// ---------------------------------------------------------------------------
// Static pieces
// ---------------------------------------------------------------------------

export const DEMO_USER = {
  id: 0,
  spotify_id: "demo-user",
  display_name: "Alex Rivera",
  email: "alex@example.com",
  images: [] as { url: string }[],
};

export const DEMO_GENRES = {
  slices: [
    { name: "Indie Pop", weight: 28, artist_count: 14 },
    { name: "Synthwave", weight: 22, artist_count: 11 },
    { name: "Dream Pop", weight: 17, artist_count: 9 },
    { name: "Lo-Fi Beats", weight: 14, artist_count: 7 },
    { name: "Alt Rock", weight: 11, artist_count: 6 },
    { name: "Other", weight: 8, artist_count: 13 },
  ],
  total_genres: 23,
  based_on_artists: 50,
};

const PLAYLIST_SPECS: [name: string, collaborative: boolean, owner: string][] = [
  ["Late Night Drive", false, "Alex Rivera"],
  ["Focus Flow", false, "Alex Rivera"],
  ["Sunday Reset", false, "Alex Rivera"],
  ["Heavy Rotation", false, "Alex Rivera"],
  ["Rainy Day Study", false, "Alex Rivera"],
  ["Road Trip Roulette", true, "Alex Rivera"],
  ["Morning Commute", false, "Alex Rivera"],
  ["Dream Pop Daydreams", false, "Alex Rivera"],
  ["Synth Cities", false, "Alex Rivera"],
  ["Gym Warmup", false, "Alex Rivera"],
  ["Cooking With Friends", true, "Jordan Lee"],
  ["Slow Burn", false, "Alex Rivera"],
  ["New Finds", false, "Alex Rivera"],
  ["Old Favourites", false, "Alex Rivera"],
  ["Coffee Shop Corners", false, "Alex Rivera"],
  ["Weekend Wind Down", false, "Alex Rivera"],
  ["Deep Focus", false, "Alex Rivera"],
  ["Sunrise Run", false, "Alex Rivera"],
];

export const DEMO_PLAYLISTS = PLAYLIST_SPECS.map(([name, collaborative, owner]) => ({
  id: `demo-playlist-${slug(name)}`,
  name,
  collaborative,
  images: [{ url: coverArt(`playlist:${name}`) }],
  external_urls: { spotify: "https://open.spotify.com" },
  owner: { display_name: owner },
}));

export const DEMO_ARTISTS = ARTISTS;
export const DEMO_TRACKS = TRACKS;
