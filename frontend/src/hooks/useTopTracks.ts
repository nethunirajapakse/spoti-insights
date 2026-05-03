import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getTopTracks } from "@/api/analytics";

export const useTopTracks = (timeRange: string, limit: number) => {
  const queryClient = useQueryClient();
  const queryKey = ["topTracks", timeRange, limit];

  const {
    data: topTracksData,
    isFetching: isTopTracksFetching,
    error: topTracksError,
  } = useQuery({
    queryKey,
    queryFn: () => getTopTracks(timeRange, limit),
    placeholderData: (previousData) => previousData,
  });

  const refreshTopTracks = () => queryClient.invalidateQueries({ queryKey });

  return {
    topTracksData,
    isTopTracksFetching,
    topTracksError,
    refreshTopTracks,
  };
};
