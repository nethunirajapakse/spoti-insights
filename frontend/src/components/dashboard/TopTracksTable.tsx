import { useState } from "react";
import { Link } from "react-router-dom";
import { useTopItems } from "@/hooks/useTopItems";

type TimeRange = "short_term" | "medium_term" | "long_term";

interface Track {
  id: string;
  name: string;
  artists: { name: string }[];
  duration_ms: number;
  album?: { images?: { url: string }[] };
}

const RANGE_LABELS: Record<TimeRange, string> = {
  short_term: "4 weeks",
  medium_term: "6 months",
  long_term: "All time",
};

const formatDuration = (ms: number) => {
  const totalSec = Math.floor(ms / 1000);
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  return `${min}:${sec.toString().padStart(2, "0")}`;
};

export const TopTracksTable = () => {
  const [range, setRange] = useState<TimeRange>("short_term");
  const { topItemsData, isTopItemsFetching } = useTopItems("tracks", range, 5);

  return (
    <div className="glass-card rounded-3xl p-6 sm:p-8 flex flex-col">
      <div className="flex items-center justify-between mb-6 gap-4 flex-wrap">
        <h3 className="text-xl font-bold text-white">Top Tracks</h3>
        <div className="flex gap-1 bg-white/5 rounded-full p-1">
          {(Object.keys(RANGE_LABELS) as TimeRange[]).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRange(r)}
              className={`px-3 py-1 rounded-full text-[11px] font-bold transition-colors ${
                range === r
                  ? "bg-primary text-on-primary"
                  : "text-on-surface-variant hover:text-white"
              }`}
            >
              {RANGE_LABELS[r]}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="text-outline uppercase text-[10px] tracking-widest border-b border-white/5">
              <th className="pb-3 font-bold w-8">#</th>
              <th className="pb-3 font-bold">Title</th>
              <th className="pb-3 font-bold hidden sm:table-cell">Artist</th>
              <th className="pb-3 font-bold text-right">Duration</th>
            </tr>
          </thead>
          <tbody className="text-sm">
            {isTopItemsFetching && !topItemsData ? (
              Array.from({ length: 5 }, (_, i) => (
                <tr key={`track-skel-${i}`}>
                  <td colSpan={4} className="py-3">
                    <div className="h-10 bg-white/[0.02] rounded animate-pulse" />
                  </td>
                </tr>
              ))
            ) : !topItemsData?.items?.length ? (
              <tr>
                <td
                  colSpan={4}
                  className="py-8 text-center text-on-surface-variant"
                >
                  No tracks yet for this range.
                </td>
              </tr>
            ) : (
              topItemsData.items.map((track: Track, i: number) => (
                <tr
                  key={track.id}
                  className="group hover:bg-white/[0.02] transition-colors border-b border-white/[0.02] last:border-0"
                >
                  <td className="py-3 text-outline font-bold w-8">{i + 1}</td>
                  <td className="py-3">
                    <div className="flex items-center gap-3 min-w-0">
                      {track.album?.images?.[2]?.url && (
                        <img
                          src={track.album.images[2].url}
                          alt=""
                          className="w-10 h-10 rounded-md object-cover flex-shrink-0 hidden sm:block"
                        />
                      )}
                      <div className="min-w-0">
                        <p className="font-bold text-white group-hover:text-primary transition-colors line-clamp-1">
                          {track.name}
                        </p>
                        <p className="text-[11px] text-on-surface-variant line-clamp-1 sm:hidden">
                          {track.artists[0]?.name}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 text-on-surface-variant line-clamp-1 hidden sm:table-cell">
                    {track.artists[0]?.name}
                  </td>
                  <td className="py-3 text-right text-outline font-mono whitespace-nowrap">
                    {formatDuration(track.duration_ms)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-4 pt-4 border-t border-white/5 flex justify-end">
        <Link
          to="/history"
          className="text-primary text-xs font-bold hover:underline"
        >
          View full history →
        </Link>
      </div>
    </div>
  );
};
