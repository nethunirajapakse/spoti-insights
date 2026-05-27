import { Clock } from "lucide-react";
import { useRecentlyPlayed } from "@/hooks/useRecentlyPlayed";

interface RecentlyPlayedItem {
  track: {
    id: string;
    name: string;
    artists: { name: string }[];
    album: { images: { url: string }[] };
  };
  played_at: string;
}

const formatRelative = (iso: string): string => {
  const then = new Date(iso).getTime();
  const now = Date.now();
  const diffMin = Math.floor((now - then) / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  return `${diffDay}d ago`;
};

const SkeletonList = () => (
  <div className="space-y-3">
    {Array.from({ length: 6 }, (_, i) => (
      <div
        key={`recent-skel-${i}`}
        className="h-12 bg-white/[0.02] rounded-lg animate-pulse"
      />
    ))}
  </div>
);

const EmptyState = () => (
  <p className="text-on-surface-variant text-sm text-center py-8">
    Nothing played recently.
  </p>
);

const TrackItem = ({ item }: { item: RecentlyPlayedItem }) => (
  <li className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/[0.03] transition-colors group">
    <img
      src={item.track.album.images[2]?.url ?? item.track.album.images[0]?.url}
      alt=""
      className="w-10 h-10 rounded-md object-cover flex-shrink-0"
    />
    <div className="min-w-0 flex-1">
      <p className="text-sm font-bold text-white line-clamp-1 group-hover:text-primary transition-colors">
        {item.track.name}
      </p>
      <p className="text-[11px] text-on-surface-variant line-clamp-1">
        {item.track.artists.map((a) => a.name).join(", ")}
      </p>
    </div>
    <span className="text-[10px] text-outline font-mono flex-shrink-0">
      {formatRelative(item.played_at)}
    </span>
  </li>
);

export const RecentlyPlayedPanel = () => {
  const { recentlyPlayedData, isRecentlyPlayedFetching } = useRecentlyPlayed(8);

  const renderContent = () => {
    if (isRecentlyPlayedFetching && !recentlyPlayedData) {
      return <SkeletonList />;
    }
    if (recentlyPlayedData?.items?.length) {
      return (
        <ul className="space-y-1 flex-1 overflow-y-auto -mr-2 pr-2">
          {recentlyPlayedData.items.map((item: RecentlyPlayedItem) => (
            <TrackItem
              key={`${item.track.id}-${item.played_at}`}
              item={item}
            />
          ))}
        </ul>
      );
    }
    return <EmptyState />;
  };

  return (
    <div className="glass-card rounded-3xl p-6 flex flex-col">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-lg font-bold text-white">Recently Played</h3>
        <Clock size={14} className="text-primary" />
      </div>
      {renderContent()}
    </div>
  );
};
