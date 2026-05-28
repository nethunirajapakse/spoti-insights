import { useState } from "react";
import { ListMusic, ExternalLink, Info } from "lucide-react";
import { useUserPlaylists } from "@/hooks/useUserPlaylists";
import { DEFAULT_API_LIMIT } from "@/constants";

interface Playlist {
  id: string;
  name: string;
  images?: { url: string }[];
  external_urls: { spotify: string };
  owner: { display_name: string };
  collaborative: boolean;
}

const PlaylistCard = ({ playlist }: { playlist: Playlist }) => (
  <div className="glass-card p-5 rounded-3xl group hover:border-primary/30 transition-all duration-500 shadow-xl">
    <div className="relative aspect-square overflow-hidden rounded-2xl mb-4 shadow-2xl">
      <img
        src={playlist.images?.[0]?.url}
        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700"
        alt={playlist.name}
      />
      <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
        <a
          href={playlist.external_urls.spotify}
          target="_blank"
          rel="noopener noreferrer"
          className="p-3 bg-primary rounded-full text-black hover:scale-110 transition-transform"
        >
          <ExternalLink size={20} />
        </a>
      </div>
    </div>

    <div className="space-y-1">
      <h3 className="font-bold text-white truncate group-hover:text-primary transition-colors">
        {playlist.name}
      </h3>
      <div className="flex justify-between items-center">
        <p className="text-[10px] text-outline uppercase font-bold tracking-widest truncate">
          By {playlist.owner.display_name}
        </p>
        {playlist.collaborative && (
          <span className="text-[9px] bg-primary/20 text-primary px-2 py-0.5 rounded-full font-bold flex-shrink-0">
            Collab
          </span>
        )}
      </div>
    </div>
  </div>
);

const PlaylistLibrary = () => {
  const [offset, setOffset] = useState(0);
  const { playlistsData, isPlaylistsFetching } = useUserPlaylists(
    DEFAULT_API_LIMIT,
    offset,
  );

  const hasPrev = offset > 0;
  const hasNext = Boolean(playlistsData?.next);
  const total = playlistsData?.total ?? 0;
  const items: Playlist[] = playlistsData?.items ?? [];

  // Human-readable "showing X–Y of Z".
  const rangeStart = total === 0 ? 0 : offset + 1;
  const rangeEnd = offset + items.length;

  const goPrev = () => setOffset((o) => Math.max(0, o - DEFAULT_API_LIMIT));
  const goNext = () => setOffset((o) => o + DEFAULT_API_LIMIT);

  const renderGrid = () => {
    if (isPlaylistsFetching && items.length === 0) {
      return (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
          {Array.from({ length: 6 }, (_, i) => (
            <div
              key={`playlist-skeleton-${i}`}
              className="h-64 bg-white/5 rounded-3xl animate-pulse"
            />
          ))}
        </div>
      );
    }
    if (items.length === 0) {
      return (
        <p className="text-on-surface-variant text-sm py-16 text-center">
          No playlists found.
        </p>
      );
    }
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
        {items.map((playlist) => (
          <PlaylistCard key={playlist.id} playlist={playlist} />
        ))}
      </div>
    );
  };

  return (
    <div className="grid grid-cols-12 gap-6 lg:gap-gutter w-full">
      {/* Main grid */}
      <section className="col-span-12 lg:col-span-8 xl:col-span-9">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-black text-white tracking-tight">
            Your Library
          </h2>
        </div>
        {renderGrid()}
      </section>

      {/* Sidebar */}
      <aside className="col-span-12 lg:col-span-4 xl:col-span-3 space-y-6">
        <div className="glass-card p-8 rounded-3xl shadow-xl relative overflow-hidden">
          <div className="absolute -top-4 -right-4 opacity-5 rotate-12">
            <ListMusic size={120} />
          </div>

          <h3 className="font-bold mb-6 flex items-center gap-2 text-white text-lg">
            <Info className="text-primary" size={20} /> Library Info
          </h3>

          <div className="space-y-8">
            <div>
              <p className="text-[10px] uppercase text-outline font-black tracking-widest mb-1">
                Total Playlists
              </p>
              <div className="flex items-baseline gap-2">
                <p className="text-5xl font-black text-primary">{total}</p>
                <span className="text-xs text-outline font-bold">
                  collections
                </span>
              </div>
            </div>

            <div className="pt-6 border-t border-white/5">
              <p className="text-xs text-on-surface-variant leading-relaxed mb-6">
                Showing {rangeStart}–{rangeEnd} of {total}.
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={goPrev}
                  disabled={!hasPrev || isPlaylistsFetching}
                  className="flex-1 py-3 bg-white/5 text-white rounded-2xl font-bold text-xs disabled:opacity-30 transition-all border border-white/10 active:scale-95"
                >
                  Prev
                </button>
                <button
                  type="button"
                  onClick={goNext}
                  disabled={!hasNext || isPlaylistsFetching}
                  className="flex-1 py-3 bg-primary text-on-primary rounded-2xl font-bold text-xs disabled:opacity-30 transition-all shadow-lg shadow-primary/20 active:scale-95"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
};

export default PlaylistLibrary;
