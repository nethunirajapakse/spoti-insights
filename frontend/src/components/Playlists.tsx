import { useState, useEffect } from "react";
import { ListMusic, ExternalLink, Info, Loader2, ArrowUp, RefreshCw } from "lucide-react";
import { useUserPlaylists } from "@/hooks/useUserPlaylists";

interface Playlist {
  id: string;
  name: string;
  images?: { url: string }[];
  external_urls: { spotify: string };
  owner: { display_name: string };
  collaborative: boolean;
}

const PlaylistCard = ({ playlist }: { playlist: Playlist }) => (
  <div className="glass-card p-5 rounded-3xl group hover:border-primary/30 transition-all duration-500 shadow-xl flex flex-col justify-between h-full bg-white/[0.02] border border-white/5">
    <div>
      <div className="relative aspect-square overflow-hidden rounded-2xl mb-4 shadow-2xl bg-zinc-900">
        <img
          src={playlist.images?.[0]?.url ?? "/placeholder-art.png"}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          alt={playlist.name}
          loading="lazy"
        />
        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
          <a
            href={playlist.external_urls.spotify}
            target="_blank"
            rel="noopener noreferrer"
            className="p-3.5 bg-primary rounded-full text-black hover:scale-110 transition-transform shadow-xl"
          >
            <ExternalLink size={18} className="stroke-[2.5]" />
          </a>
        </div>
      </div>

      <h3 className="font-bold text-white text-base truncate group-hover:text-primary transition-colors mb-1">
        {playlist.name}
      </h3>
    </div>

    <div className="flex justify-between items-center mt-2 pt-2 border-t border-white/5">
      <p className="text-[10px] text-outline uppercase font-bold tracking-widest truncate max-w-[70%]">
        By {playlist.owner.display_name}
      </p>
      {playlist.collaborative && (
        <span className="text-[9px] bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded-full font-bold flex-shrink-0">
          Collab
        </span>
      )}
    </div>
  </div>
);

const PlaylistLibrary = () => {
  const {
    playlistsItems,
    totalCount,
    isPlaylistsFetching,
    isFetchingNextPage,
    fetchNextPage,
    hasNextPage,
    refreshPlaylists,
  } = useUserPlaylists(24); // Generates cleanly across 1, 2, or 3 grid setups

  const [showScrollTop, setShowScrollTop] = useState(false);
  const isInitialLoading = isPlaylistsFetching && playlistsItems.length === 0;

  useEffect(() => {
    const handleScroll = () => {
      setShowScrollTop(globalThis.scrollY > 400);
    };
    globalThis.addEventListener("scroll", handleScroll);
    return () => globalThis.removeEventListener("scroll", handleScroll);
  }, []);

  const renderGrid = () => {
    if (isInitialLoading) {
      return (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
          {Array.from({ length: 6 }, (_, i) => (
            <div
              key={`playlist-skeleton-${i}`}
              className="aspect-[4/5] bg-white/[0.02] border border-white/5 rounded-3xl animate-pulse flex flex-col p-5"
            >
              <div className="aspect-square w-full bg-white/5 rounded-2xl mb-4" />
              <div className="h-4 bg-white/10 rounded w-3/4 mb-2" />
              <div className="h-3 bg-white/5 rounded w-1/2 mt-auto" />
            </div>
          ))}
        </div>
      );
    }

    if (playlistsItems.length === 0) {
      return (
        <div className="glass-card py-20 text-center rounded-3xl border border-white/5">
          <p className="text-outline text-sm">No collections found inside your playlist ecosystem.</p>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
        {playlistsItems.map((playlist) => (
          <PlaylistCard key={playlist.id} playlist={playlist} />
        ))}
      </div>
    );
  };

  return (
    <div className="grid grid-cols-12 gap-6 lg:gap-8 items-start relative w-full">
      
      {/* Primary Collections Grid */}
      <section className="col-span-12 lg:col-span-8 xl:col-span-9 order-2 lg:order-1">
        {renderGrid()}

        {/* Load More Trigger Control */}
        {hasNextPage && (
          <div className="mt-8 flex justify-center">
            <button
              type="button"
              onClick={() => fetchNextPage()}
              disabled={isFetchingNextPage}
              className="flex items-center gap-2 px-8 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-xs font-black uppercase tracking-widest text-outline hover:text-white transition-all active:scale-95 disabled:opacity-50 shadow-xl"
            >
              {isFetchingNextPage ? (
                <>
                  <Loader2 size={14} className="animate-spin" /> Fetching Libraries…
                </>
              ) : (
                "Load More Playlists"
              )}
            </button>
          </div>
        )}
      </section>

      {/* Sidebar Control Deck */}
      <aside className="col-span-12 lg:col-span-4 xl:col-span-3 order-1 lg:order-2 flex flex-col gap-4 lg:gap-6 lg:sticky lg:top-6">
        
        {/* Full-width Instant Sync Switch */}
        <div className="w-full">
          <button
            type="button"
            onClick={refreshPlaylists}
            disabled={isPlaylistsFetching}
            className="flex items-center justify-center gap-2 px-4 py-3.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl transition-all active:scale-[0.99] disabled:opacity-50 group w-full shadow-xl"
          >
            <span className="text-[10px] uppercase tracking-widest font-black text-outline group-hover:text-white transition-colors">
              {isPlaylistsFetching ? "Syncing Grid" : "Refresh Library"}
            </span>
            <RefreshCw
              size={14}
              className={`text-primary ${isPlaylistsFetching ? "animate-spin" : ""}`}
            />
          </button>
        </div>

        {/* Library Info Card Block */}
        <div className="glass-card p-6 sm:p-8 rounded-2xl shadow-xl relative overflow-hidden border border-white/5">
          <div className="absolute -top-4 -right-4 opacity-5 rotate-12 text-white pointer-events-none">
            <ListMusic size={120} />
          </div>

          <h3 className="font-black mb-6 flex items-center gap-2 text-white text-xs uppercase tracking-widest">
            <Info className="text-primary" size={16} /> Library Metadata
          </h3>

          <div className="space-y-6">
            <div>
              <p className="text-[10px] uppercase text-outline font-black tracking-widest mb-1">
                Total Playlists
              </p>
              <div className="flex items-baseline gap-2 leading-none">
                <p className="text-4xl font-black text-primary leading-none">{totalCount}</p>
                <span className="text-[10px] text-outline font-bold uppercase tracking-wider">
                  Collections
                </span>
              </div>
            </div>

            <div className="pt-6 border-t border-white/5">
              <p className="text-[11px] text-on-surface-variant leading-relaxed">
                Currently tracking <span className="text-white font-bold">{playlistsItems.length}</span> collections. Use the infinite query controller to append remaining listings down line.
              </p>
            </div>
          </div>
        </div>
      </aside>

      {/* Floating Scroll Top Trigger */}
      <button
        type="button"
        onClick={() => globalThis.scrollTo({ top: 0, behavior: "smooth" })}
        className={`fixed bottom-6 right-6 p-3 bg-primary hover:bg-primary-hover text-black rounded-full shadow-2xl transition-all duration-300 z-50 hover:scale-110 active:scale-90 ${
          showScrollTop 
            ? "opacity-100 translate-y-0" 
            : "opacity-0 translate-y-4 pointer-events-none"
        }`}
        aria-label="Scroll to top"
      >
        <ArrowUp size={18} className="stroke-[3]" />
      </button>

    </div>
  );
};

export default PlaylistLibrary;
