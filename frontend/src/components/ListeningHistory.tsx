import { useState, useEffect } from "react";
import { TrendingUp, RefreshCw, Loader2, ArrowUp } from "lucide-react";
import { useHistory } from "@/hooks/useHistory";
import { useTodaySummary } from "@/hooks/useTodaySummary";
import type { HistoryItem } from "@/api/analytics";

const HISTORY_PAGE_SIZE = 20;

const formatDuration = (ms: number) => {
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  return `${minutes}:${seconds < 10 ? "0" : ""}${seconds}`;
};

const formatRelative = (iso: string): string => {
  const then = new Date(iso).getTime();
  const diffMin = Math.floor((Date.now() - then) / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 7) return `${diffDay}d ago`;
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
};

const HistoryRow = ({ item }: { item: HistoryItem }) => (
  <tr className="hover:bg-white/[0.03] transition-colors group">
    <td className="px-6 py-4">
      <div className="flex items-center gap-4">
        <img
          src={item.album_art_url}
          className="w-10 h-10 rounded shadow-lg group-hover:scale-105 transition-transform flex-shrink-0"
          alt=""
        />
        <div className="flex flex-col min-w-0">
          <span className="font-bold text-white group-hover:text-primary transition-colors line-clamp-1">
            {item.track_name}
          </span>
          <span className="text-[10px] text-outline flex items-center gap-1">
            {formatRelative(item.played_at)}
          </span>
        </div>
      </div>
    </td>
    <td className="px-6 py-4 text-sm text-on-surface-variant line-clamp-1">
      {item.artist_name}
    </td>
    <td className="px-6 py-4 text-sm text-on-surface-variant hidden md:table-cell">
      {item.album_name}
    </td>
    <td className="px-6 py-4 text-sm text-outline text-right font-mono whitespace-nowrap">
      {formatDuration(item.duration_ms)}
    </td>
  </tr>
);

const ListeningHistory = () => {
  const {
    historyItems,
    totalCount,
    isHistoryFetching,
    isFetchingNextPage,
    fetchNextPage,
    hasNextPage,
    refreshHistory,
  } = useHistory(HISTORY_PAGE_SIZE);

  const { todaySummaryData } = useTodaySummary();
  const [showScrollTop, setShowScrollTop] = useState(false);

  const isInitialLoading = isHistoryFetching && historyItems.length === 0;

  // Track scroll position to reveal the "Scroll to Top" button
  useEffect(() => {
    const handleScroll = () => {
      if (globalThis.scrollY > 400) {
        setShowScrollTop(true);
      } else {
        setShowScrollTop(false);
      }
    };

    globalThis.addEventListener("scroll", handleScroll);
    return () => globalThis.removeEventListener("scroll", handleScroll);
  }, []);

  const scrollToTop = () => {
    globalThis.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  return (
    <div className="grid grid-cols-12 gap-6 lg:gap-8 items-start relative">
      {/* Primary Table Segment */}
      <section className="col-span-12 lg:col-span-9 order-2 lg:order-1">
        <div className="glass-card rounded-2xl overflow-hidden shadow-2xl">
          <table className="w-full text-left border-collapse">
            <thead className="bg-white/[0.02] text-[10px] uppercase tracking-widest text-outline border-b border-white/5">
              <tr>
                <th className="px-6 py-5 font-bold">Track</th>
                <th className="px-6 py-5 font-bold">Artist</th>
                <th className="px-6 py-5 font-bold hidden md:table-cell">
                  Album
                </th>
                <th className="px-6 py-5 font-bold text-right">Dur.</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {isInitialLoading ? (
                <tr>
                  <td
                    colSpan={4}
                    className="p-20 text-center animate-pulse text-outline text-xs uppercase tracking-widest"
                  >
                    Loading your listening history…
                  </td>
                </tr>
              ) : historyItems.length === 0 ? (
                <tr>
                  <td
                    colSpan={4}
                    className="p-20 text-center text-outline text-sm"
                  >
                    No listening history yet. Play some music on Spotify and it
                    will sync here.
                  </td>
                </tr>
              ) : (
                historyItems.map((item) => (
                  <HistoryRow key={`${item.id}`} item={item} />
                ))
              )}
            </tbody>
          </table>

          {/* Load More Button Wrapper */}
          {hasNextPage && (
            <div className="p-4 flex justify-center border-t border-white/5">
              <button
                type="button"
                onClick={() => fetchNextPage()}
                disabled={isFetchingNextPage}
                className="flex items-center gap-2 px-6 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-xs font-bold text-on-surface-variant hover:text-white transition-all active:scale-95 disabled:opacity-50"
              >
                {isFetchingNextPage ? (
                  <>
                    <Loader2 size={14} className="animate-spin" /> Loading…
                  </>
                ) : (
                  "Load More"
                )}
              </button>
            </div>
          )}
        </div>

        {/* Total Count Metrics */}
        {historyItems.length > 0 && (
          <p className="text-[11px] text-outline text-center mt-4">
            Showing {historyItems.length} of {totalCount.toLocaleString()}{" "}
            tracks
          </p>
        )}
      </section>

      {/* Sidebar Control Deck */}
      <aside className="col-span-12 lg:col-span-3 order-1 lg:order-2 flex flex-col gap-4 lg:gap-6 lg:sticky lg:top-6">
        {/* Utilities Wrapper - Snaps to the same length as the card */}
        <div className="w-full">
          <button
            type="button"
            onClick={refreshHistory}
            disabled={isHistoryFetching}
            className="flex items-center justify-center gap-2 px-4 py-3.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-2xl transition-all active:scale-[0.99] disabled:opacity-50 group w-full shadow-xl"
          >
            <span className="text-[10px] uppercase tracking-widest font-black text-outline group-hover:text-white transition-colors">
              {isHistoryFetching ? "Syncing History" : "Refresh"}
            </span>
            <RefreshCw
              size={14}
              className={`text-primary ${isHistoryFetching ? "animate-spin" : ""}`}
            />
          </button>
        </div>

        {/* Analytics Card */}
        <div className="glass-card p-6 rounded-2xl shadow-xl w-full">
          <h3 className="font-bold mb-6 flex items-center gap-2 text-white">
            <TrendingUp className="text-primary" size={18} /> Today's Activity
          </h3>
          <div className="space-y-6">
            <div>
              <p className="text-[10px] uppercase text-outline font-bold tracking-wider mb-1">
                Tracks Today
              </p>
              <p className="text-4xl font-black text-primary leading-none">
                {todaySummaryData?.total_tracks ?? 0}
              </p>
            </div>
            <div>
              <p className="text-[10px] uppercase text-outline font-bold tracking-wider mb-1">
                Listening Time
              </p>
              <p className="text-2xl font-bold text-white leading-none">
                {todaySummaryData?.listening_time ?? "0h 0m"}
              </p>
            </div>
            <div className="pt-6 border-t border-white/5">
              <p className="text-[11px] text-on-surface-variant leading-relaxed">
                Your full play history is synced from Spotify every 15 minutes
                and stored for long-term analytics.
              </p>
            </div>
          </div>
        </div>
      </aside>

      {/* Floating Scroll-to-Top Action Button */}
      <button
        type="button"
        onClick={scrollToTop}
        className={`fixed bottom-6 right-6 p-3 bg-primary hover:bg-primary-hover text-black rounded-full shadow-2xl transition-all duration-300 z-50 hover:scale-110 active:scale-90 ${
          showScrollTop
            ? "opacity-100 translate-y-0 pointer-events-auto"
            : "opacity-0 translate-y-4 pointer-events-none"
        }`}
        aria-label="Scroll to top"
      >
        <ArrowUp size={18} className="stroke-[3]" />
      </button>
    </div>
  );
};

export default ListeningHistory;
