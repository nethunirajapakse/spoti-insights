import { TrendingUp, Clock, RefreshCw } from 'lucide-react';
import { useRecentlyPlayed } from "@/hooks/useRecentlyPlayed";
import { DEFAULT_API_LIMIT } from '@/constants';

const ListeningHistory = () => {
  const { 
    recentlyPlayedData, 
    isRecentlyPlayedFetching, 
    refreshRecentlyPlayed 
  } = useRecentlyPlayed(DEFAULT_API_LIMIT);

  const formatDuration = (ms: number) => {
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
  };

  return (
    <div className="grid grid-cols-12 gap-8">
      <section className="col-span-12 lg:col-span-9">
        
        {/* Modern Clean Header Level with Action */}
        <div className="flex justify-between items-end mb-6 px-2">
          <div>
            <h2 className="text-[10px] uppercase tracking-[0.2em] text-primary font-bold mb-1">
              Data Stream
            </h2>
            <h1 className="text-2xl font-black text-white">Listening History</h1>
          </div>
          
          <button 
            onClick={refreshRecentlyPlayed}
            disabled={isRecentlyPlayedFetching}
            className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-all active:scale-95 disabled:opacity-50 group"
          >
            <span className="text-[10px] uppercase tracking-widest font-bold text-outline group-hover:text-white transition-colors">
              {isRecentlyPlayedFetching ? 'Syncing' : 'Refresh'}
            </span>
            <RefreshCw 
              size={14} 
              className={`text-primary ${isRecentlyPlayedFetching ? 'animate-spin' : ''}`} 
            />
          </button>
        </div>

        {/* The Table */}
        <div className="bg-white/5 backdrop-blur-2xl rounded-2xl border border-white/10 overflow-hidden shadow-2xl">
          <table className="w-full text-left border-collapse">
            <thead className="bg-white/[0.02] text-[10px] uppercase tracking-widest text-outline border-b border-white/5">
              <tr>
                <th className="px-6 py-5 font-bold">Track</th>
                <th className="px-6 py-5 font-bold">Artist</th>
                <th className="px-6 py-5 font-bold">Album</th>
                <th className="px-6 py-5 font-bold text-right">Dur.</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {!recentlyPlayedData && isRecentlyPlayedFetching ? (
                <tr>
                  <td colSpan={4} className="p-20 text-center animate-pulse text-outline text-xs uppercase tracking-widest">
                    Fetching latest sessions...
                  </td>
                </tr>
              ) : (
                recentlyPlayedData?.items.map((item: any) => {
                  const { track } = item; 
                  return (
                    <tr key={`${track.id}-${item.played_at}`} className="hover:bg-white/[0.03] transition-colors group">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-4">
                          <img 
                            src={track.album.images[2]?.url} 
                            className="w-10 h-10 rounded shadow-lg group-hover:scale-105 transition-transform" 
                            alt="cover" 
                          />
                          <div className="flex flex-col">
                            <span className="font-bold text-white group-hover:text-primary transition-colors line-clamp-1">
                              {track.name}
                            </span>
                            <span className="text-[10px] text-outline flex items-center gap-1">
                              <Clock size={10} /> {new Date(item.played_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-on-surface-variant line-clamp-1">
                        {track.artists.map((a: any) => a.name).join(", ")}
                      </td>
                      <td className="px-6 py-4 text-sm text-on-surface-variant">
                        {track.album.name}
                      </td>
                      <td className="px-6 py-4 text-sm text-outline text-right font-mono">
                        {formatDuration(track.duration_ms)}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Sidebar - Remains consistent */}
      <aside className="col-span-12 lg:col-span-3 space-y-6">
        <div className="glass-card p-6 rounded-2xl border border-white/10 shadow-xl">
          <h3 className="font-bold mb-6 flex items-center gap-2 text-white">
            <TrendingUp className="text-primary" size={18} /> Insights
          </h3>
          <div className="space-y-6">
            <div>
              <p className="text-[10px] uppercase text-outline font-bold tracking-wider mb-1">Session Tracks</p>
              <p className="text-4xl font-black text-primary">
                {recentlyPlayedData?.items.length || 0}
              </p>
            </div>
            <div className="pt-6 border-t border-white/5">
              <p className="text-[11px] text-on-surface-variant leading-relaxed mb-6">
                {isRecentlyPlayedFetching ? "Syncing with Spotify..." : "Your listening data is processed and cached for performance."}
              </p>
              <button className="w-full py-3 bg-primary text-black rounded-xl font-bold text-xs uppercase tracking-widest hover:brightness-110 active:scale-95 transition-all shadow-lg shadow-primary/20">
                Export Analysis
              </button>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
};

export default ListeningHistory;
