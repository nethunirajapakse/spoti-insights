import { TrendingUp } from 'lucide-react';
import { useTopTracks } from "@/hooks/useTopTracks";

const ListeningHistory = () => {
  const { data: tracksData, isLoading } = useTopTracks("medium_term", 10);

  const formatDuration = (ms: number) => {
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(0);
    return `${minutes}:${Number(seconds) < 10 ? '0' : ''}${seconds}`;
  };

  return (
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
  );
};

export default ListeningHistory;
