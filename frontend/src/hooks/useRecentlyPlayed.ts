import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getRecentlyPlayed } from "@/api/analytics";

export const useRecentlyPlayed = (limit: number) => {
  const queryClient = useQueryClient();
  const queryKey = ["recentlyPlayed", limit];

  const {
    data: recentlyPlayedData,
    isFetching: isRecentlyPlayedFetching,
    error: recentlyPlayedError,
  } = useQuery({
    queryKey,
    queryFn: () => getRecentlyPlayed(limit),
    placeholderData: (previousData) => previousData,
  });

  const refreshRecentlyPlayed = () => queryClient.invalidateQueries({ queryKey });

  return {
    recentlyPlayedData,
    isRecentlyPlayedFetching,
    recentlyPlayedError,
    refreshRecentlyPlayed,
  };
};