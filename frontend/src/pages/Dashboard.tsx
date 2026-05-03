import {
  Calendar,
  Play,
  SkipBack,
  SkipForward,
  Shuffle,
  Repeat,
  Zap,
} from "lucide-react";
import { StatCard } from "@/components/dashboard/StatCard";
import { useTopItems } from "@/hooks/useTopItems";
import { useCurrentUser } from "@/hooks/useCurrentUser";

const Dashboard = () => {
  const { data: user } = useCurrentUser();

  const {
    topItemsData: topArtistData,
    isTopItemsFetching: isTopArtistFetching,
  } = useTopItems("artists", "long_term", 1);
  const topArtist = topArtistData?.items?.[0];

  const {
    topItemsData: topTracksData,
    isTopItemsFetching: isTopTracksFetching,
  } = useTopItems("tracks", "short_term", 5);

  return (
    <div className="w-full space-y-8">
      {/* Hero Section */}
      <section className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-4xl font-black text-white tracking-tight">
            Hello, {user?.display_name?.split(" ")[0] || "User"}
          </h1>
          <p className="text-on-surface-variant font-medium">
            Your listening metrics are trending upward.
          </p>
        </div>
        <div className="glass-card flex items-center gap-3 px-4 py-2 rounded-xl text-xs font-bold border border-white/5 shadow-lg">
          <Calendar size={14} className="text-primary" />
          <span className="text-white">Live Analytics Feed</span>
        </div>
      </section>

      {/* Stats Grid */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          label="Top Artist"
          value={isTopArtistFetching ? "Loading..." : (topArtist?.name ?? "—")}
          subValue={
            isTopArtistFetching
              ? ""
              : topArtist?.genres?.[0]
                ? `Genre: ${topArtist.genres[0]}`
                : topArtist?.popularity
                  ? `Popularity: ${topArtist.popularity}`
                  : ""
          }
          image={topArtist?.images?.[0]?.url}
        />
        <StatCard
          label="Top Genre"
          value="Hip-Hop / Rap"
          trend="↑ 4% this week"
        />
        <StatCard
          label="Weekly Hours"
          value="42.5 hrs"
          trend="+12% vs last week"
        />
        <StatCard label="Streams" value="1,240" subValue="85 unique artists" />
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Now Playing */}
        <div className="lg:col-span-4 glass-card p-8 rounded-3xl flex flex-col justify-between group shadow-2xl">
          <div className="relative mb-6 aspect-square overflow-hidden rounded-2xl">
            <img
              src="https://i.scdn.co/image/ab67616d0000b273701ca963ef008e063836d5e2"
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              alt="Cover"
            />
          </div>
          <div className="text-center mb-6">
            <h3 className="text-xl font-bold text-white">Kill Bill</h3>
            <p className="text-primary text-sm font-semibold">SZA — SOS</p>
          </div>
          <div className="flex items-center justify-between px-2">
            <Shuffle
              size={18}
              className="text-outline cursor-pointer hover:text-primary"
            />
            <SkipBack size={24} className="text-white cursor-pointer" />
            <button className="bg-primary p-3 rounded-full text-black shadow-lg shadow-primary/20 active:scale-90 transition-transform">
              <Play fill="currentColor" size={24} />
            </button>
            <SkipForward size={24} className="text-white cursor-pointer" />
            <Repeat
              size={18}
              className="text-outline cursor-pointer hover:text-primary"
            />
          </div>
        </div>

        {/* Top Tracks */}
        <div className="lg:col-span-8 glass-card p-8 rounded-3xl flex flex-col shadow-xl border border-white/5">
          <h3 className="text-xl font-bold text-white mb-6">Top Tracks</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="text-[10px] text-outline uppercase tracking-widest border-b border-white/5">
                <tr>
                  <th className="pb-4">#</th>
                  <th className="pb-4">Title</th>
                  <th className="pb-4">Artist</th>
                  <th className="pb-4 text-right">Time</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {isTopTracksFetching ? (
                  <tr>
                    <td colSpan={4} className="py-10 text-center animate-pulse">
                      Loading tracks...
                    </td>
                  </tr>
                ) : (
                  topTracksData?.items?.map((track: any, i: number) => (
                    <tr
                      key={track.id}
                      className="group hover:bg-white/[0.02] transition-colors border-b border-white/[0.02] last:border-0"
                    >
                      <td className="py-4 text-outline font-bold">{i + 1}</td>
                      <td className="py-4 font-bold text-white group-hover:text-primary transition-colors">
                        {track.name}
                      </td>
                      <td className="py-4 text-on-surface-variant">
                        {track.artists[0].name}
                      </td>
                      <td className="py-4 text-right text-outline font-mono">
                        {Math.floor(track.duration_ms / 60000)}:
                        {String(
                          Math.floor((track.duration_ms % 60000) / 1000),
                        ).padStart(2, "0")}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <div className="mt-auto pt-6">
            <div className="bg-primary/10 rounded-2xl p-4 flex items-center justify-between border border-primary/20">
              <div className="flex items-center gap-3">
                <Zap size={16} className="text-primary fill-primary" />
                <p className="text-[11px] text-white">
                  We recommend a{" "}
                  <span className="text-primary font-bold">
                    Late Night Vibe
                  </span>{" "}
                  report based on this week.
                </p>
              </div>
              <button className="bg-primary text-on-primary text-[10px] font-bold px-3 py-1.5 rounded-full hover:scale-105 transition-transform">
                Explore
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Dashboard;
