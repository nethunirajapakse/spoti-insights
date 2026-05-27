import { Music2, Disc3, Clock, Users } from "lucide-react";
import type { OverviewResponse, TopEntity } from "@/api/analytics";

interface StatRowProps {
  data?: OverviewResponse;
  isLoading: boolean;
}

const SkeletonCard = () => (
  <div className="glass-card p-6 rounded-2xl h-40 animate-pulse" />
);

// Avatar rendering pulled out so the JSX doesn't need a nested ternary.
const TopArtistAvatar = ({ artist }: { artist: TopEntity | null }) => {
  if (!artist) return null;
  if (artist.image_url) {
    return (
      <img
        src={artist.image_url}
        alt={artist.name}
        className="w-14 h-14 rounded-full object-cover border-2 border-primary/20 flex-shrink-0"
      />
    );
  }
  return (
    <div className="w-14 h-14 rounded-full border-2 border-primary/20 bg-white/5 flex items-center justify-center text-lg font-bold text-primary flex-shrink-0">
      {artist.name.charAt(0).toUpperCase()}
    </div>
  );
};

export const StatRow = ({ data, isLoading }: StatRowProps) => {
  if (isLoading || !data) {
    return (
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-gutter">
        {Array.from({ length: 4 }, (_, i) => (
          <SkeletonCard key={`stat-skeleton-${i}`} />
        ))}
      </section>
    );
  }

  const { total_tracks, total_hours, unique_artists, top_artist, top_track } =
    data;

  return (
    <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-gutter">
      {/* Top Artist */}
      <div className="glass-card p-6 rounded-2xl h-40 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <p className="text-[10px] uppercase tracking-widest font-bold text-on-surface-variant">
            Top Artist
          </p>
          <Users size={14} className="text-primary" />
        </div>
        <div className="flex items-center gap-4">
          <TopArtistAvatar artist={top_artist} />
          <div className="min-w-0">
            <p className="text-lg font-bold text-white leading-tight line-clamp-2">
              {top_artist?.name ?? "—"}
            </p>
            {top_artist && (
              <p className="text-primary text-xs font-bold mt-0.5">
                {top_artist.play_count} plays
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Top Track */}
      <div className="glass-card p-6 rounded-2xl h-40 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <p className="text-[10px] uppercase tracking-widest font-bold text-on-surface-variant">
            Top Track
          </p>
          <Music2 size={14} className="text-primary" />
        </div>
        <div className="flex items-center gap-3">
          {top_track?.image_url && (
            <img
              src={top_track.image_url}
              alt=""
              className="w-12 h-12 rounded-lg object-cover flex-shrink-0"
            />
          )}
          <div className="min-w-0">
            <p className="text-base font-bold text-white leading-tight line-clamp-1">
              {top_track?.name ?? "—"}
            </p>
            {top_track && (
              <p className="text-[11px] text-on-surface-variant line-clamp-1 mt-0.5">
                {top_track.artist_name}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Listening Hours */}
      <div className="glass-card p-6 rounded-2xl h-40 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <p className="text-[10px] uppercase tracking-widest font-bold text-on-surface-variant">
            Listening Time
          </p>
          <Clock size={14} className="text-primary" />
        </div>
        <div>
          <p className="text-[40px] leading-none font-bold text-white">
            {total_hours.toFixed(1)}
            <span className="text-base text-on-surface-variant font-medium ml-1">
              hrs
            </span>
          </p>
          <p className="text-[11px] text-on-surface-variant mt-2">
            Last {data.window_days} days
          </p>
        </div>
      </div>

      {/* Streams */}
      <div className="glass-card p-6 rounded-2xl h-40 flex flex-col justify-between">
        <div className="flex items-center justify-between">
          <p className="text-[10px] uppercase tracking-widest font-bold text-on-surface-variant">
            Total Streams
          </p>
          <Disc3 size={14} className="text-primary" />
        </div>
        <div>
          <p className="text-[40px] leading-none font-bold text-white">
            {total_tracks.toLocaleString()}
          </p>
          <p className="text-[11px] text-on-surface-variant mt-2">
            Across {unique_artists} unique artists
          </p>
        </div>
      </div>
    </section>
  );
};
