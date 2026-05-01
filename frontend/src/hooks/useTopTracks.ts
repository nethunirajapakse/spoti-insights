import { useQuery } from "@tanstack/react-query";
import { getTopTracks } from "@/api/analytics";

export const useTopTracks = (timeRange?: string, limit?: number) => {
  return useQuery({
    queryKey: ["topTracks", timeRange, limit],
    queryFn: () => getTopTracks(timeRange, limit),
    placeholderData: (previousData) => previousData,
  });
};
