import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getGenreDistribution } from "@/api/analytics";

export const useGenreDistribution = (top_n = 5) => {
  const queryClient = useQueryClient();
  const queryKey = ["genreDistribution", top_n];

  const {
    data: genreDistributionData,
    isFetching: isGenreDistributionFetching,
    error: genreDistributionError,
  } = useQuery({
    queryKey,
    queryFn: () => getGenreDistribution(top_n),
    placeholderData: (previousData) => previousData,
    staleTime: 1000 * 60 * 15, // Genres change slowly
  });

  const refreshGenreDistribution = () =>
    queryClient.invalidateQueries({ queryKey });

  return {
    genreDistributionData,
    isGenreDistributionFetching,
    genreDistributionError,
    refreshGenreDistribution,
  };
};
