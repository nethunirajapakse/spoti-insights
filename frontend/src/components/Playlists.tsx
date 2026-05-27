import { ListMusic, ExternalLink, Info, Plus } from 'lucide-react';
import { useUserPlaylists } from "@/hooks/useUserPlaylists";
import { DEFAULT_API_LIMIT, DEFAULT_OFFSET } from '@/constants';

const PlaylistLibrary = () => {
  const { playlistsData, isPlaylistsFetching } = useUserPlaylists(DEFAULT_API_LIMIT, DEFAULT_OFFSET);

  return (
    <div className="grid grid-cols-12 gap-gutter w-full">
      {/* Main Grid Section */}
      <section className="col-span-12 lg:col-span-8 xl:col-span-9">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-black text-white tracking-tight">Your Library</h2>
          <button className="flex items-center gap-2 bg-white/5 hover:bg-white/10 text-white text-xs font-bold px-4 py-2 rounded-full border border-white/10 transition-all">
            <Plus size={14} /> New Playlist
          </button>
        </div>

        {isPlaylistsFetching ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
            {Array.from({ length: 6 }, (_, i) => (
              <div
                key={`playlist-skeleton-${i}`}
                className="h-64 bg-white/5 rounded-3xl animate-pulse border border-white/5"
              />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
            {playlistsData?.items.map((playlist: any) => (
              <div key={playlist.id} className="glass-card p-5 rounded-3xl group hover:border-primary/30 transition-all duration-500 shadow-xl">
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
                    <p className="text-[10px] text-outline uppercase font-bold tracking-widest">
                      By {playlist.owner.display_name}
                    </p>
                    {playlist.collaborative && (
                      <span className="text-[9px] bg-primary/20 text-primary px-2 py-0.5 rounded-full font-bold">Collab</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Sidebar Insights */}
      <aside className="col-span-12 lg:col-span-4 xl:col-span-3 space-y-6">
        <div className="glass-card p-8 rounded-3xl border border-white/5 shadow-xl relative overflow-hidden">
          <div className="absolute -top-4 -right-4 opacity-5 rotate-12">
             <ListMusic size={120} />
          </div>
          
          <h3 className="font-bold mb-6 flex items-center gap-2 text-white text-lg">
            <Info className="text-primary" size={20} /> Library Info
          </h3>
          
          <div className="space-y-8">
            <div>
              <p className="text-[10px] uppercase text-outline font-black tracking-widest mb-1">Total Playlists</p>
              <div className="flex items-baseline gap-2">
                <p className="text-5xl font-black text-primary">{playlistsData?.total || 0}</p>
                <span className="text-xs text-outline font-bold">collections</span>
              </div>
            </div>

            <div className="pt-6 border-t border-white/5">
              <p className="text-xs text-on-surface-variant leading-relaxed mb-6">
                Showing {playlistsData?.items.length} playlists starting from offset {playlistsData?.offset}.
              </p>
              <div className="flex gap-2">
                <button 
                   disabled={!playlistsData?.previous}
                   className="flex-1 py-3 bg-white/5 text-white rounded-2xl font-bold text-xs disabled:opacity-30 transition-all border border-white/10"
                >
                  Prev
                </button>
                <button 
                   disabled={!playlistsData?.next}
                   className="flex-1 py-3 bg-primary text-on-primary rounded-2xl font-bold text-xs disabled:opacity-30 transition-all shadow-lg shadow-primary/20"
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
