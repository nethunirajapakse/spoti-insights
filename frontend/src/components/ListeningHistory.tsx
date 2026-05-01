import { 
  BarChart3, History, Settings, HelpCircle, Search, 
  Bell, Calendar, ChevronDown, Filter, Download, 
  TrendingUp, Zap, ChevronLeft, ChevronRight 
} from 'lucide-react';
import { useTopTracks } from "@/hooks/useTopTracks";
import { useCurrentUser } from "@/hooks/useCurrentUser";

const ListeningHistory = () => {
  const { data: userData } = useCurrentUser();
  const { data: tracksData, isLoading, isError } = useTopTracks("medium_term", 10);

  const formatDuration = (ms: number) => {
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(0);
    return `${minutes}:${Number(seconds) < 10 ? '0' : ''}${seconds}`;
  };

  return (
    <div className="min-h-screen bg-[#0e150e] text-[#dde5d9] font-sans">
      {/* Sidebar - Consistent with your existing NavLink style */}
      <aside className="fixed left-0 top-0 h-full w-64 bg-[#1a211a]/40 backdrop-blur-xl border-r border-white/10 z-40 flex flex-col">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-[#53e076]">Spoti-Insights</h1>
        </div>
        <nav className="flex-1 px-4 space-y-2">
          <button className="flex w-full items-center gap-3 px-4 py-3 text-[#bccbb9] hover:bg-white/5 rounded-lg">
            <BarChart3 size={20} /> <span>Artist Insights</span>
          </button>
          <button className="flex w-full items-center gap-3 px-4 py-3 bg-[#53e076]/10 text-[#53e076] font-bold border-l-4 border-[#53e076] rounded-lg">
            <History size={20} /> <span>Listening History</span>
          </button>
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="ml-64 p-8">
        <header className="flex items-center justify-between mb-8">
          <h2 className="text-xl font-black text-[#53e076]">Top Tracks</h2>
          <div className="flex items-center gap-4">
            <span className="text-sm">{userData?.display_name || "Alex Rivera"}</span>
            <img src={userData?.images?.[0]?.url} className="w-8 h-8 rounded-full border border-[#53e076]/30" alt="avatar" />
          </div>
        </header>

        <div className="grid grid-cols-12 gap-8">
          <section className="col-span-12 lg:col-span-9">
            <div className="bg-white/5 backdrop-blur-2xl rounded-xl border border-white/10 overflow-hidden">
              <table className="w-full text-left">
                <thead className="bg-white/5 text-[10px] uppercase tracking-widest text-[#bccbb9]">
                  <tr>
                    <th className="px-6 py-4">Track</th>
                    <th className="px-6 py-4">Artist</th>
                    <th className="px-6 py-4">Album</th>
                    <th className="px-6 py-4 text-right">Dur.</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {isLoading ? (
                    <tr><td colSpan={4} className="p-10 text-center animate-pulse">Loading tracks...</td></tr>
                  ) : tracksData?.items.map((track: any) => (
                    <tr key={track.id} className="hover:bg-white/5 transition-colors group">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-4">
                          <img src={track.album.images[2]?.url} className="w-10 h-10 rounded" alt="cover" />
                          <span className="font-bold group-hover:text-[#53e076]">{track.name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-[#bccbb9]">
                        {track.artists.map((a: any) => a.name).join(", ")}
                      </td>
                      <td className="px-6 py-4 text-sm text-[#bccbb9]">{track.album.name}</td>
                      <td className="px-6 py-4 text-sm text-[#bccbb9] text-right">
                        {formatDuration(track.duration_ms)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Right Sidebar Summary */}
          <aside className="col-span-12 lg:col-span-3 space-y-6">
            <div className="bg-white/5 p-6 rounded-xl border border-white/10">
              <h3 className="font-bold mb-4 flex items-center gap-2">
                <TrendingUp className="text-[#53e076]" size={18} /> Stats
              </h3>
              <div className="space-y-4">
                <div>
                  <p className="text-[10px] uppercase text-[#bccbb9]">Total Found</p>
                  <p className="text-2xl font-black text-[#53e076]">{tracksData?.items.length || 0}</p>
                </div>
                <button className="w-full py-3 bg-[#53e076] text-[#003914] rounded-full font-bold text-sm hover:scale-[1.02] transition-transform">
                  Export Data
                </button>
              </div>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
};

export default ListeningHistory;
