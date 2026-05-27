import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getOverview } from "@/api/analytics";

export const useOverview = (days = 30) => {
  const queryClient = useQueryClient();
  const queryKey = ["overview", days];

  const {
    data: overviewData,
    isFetching: isOverviewFetching,
    error: overviewError,
  } = useQuery({
    queryKey,
    queryFn: () => getOverview(days),
    placeholderData: (previousData) => previousData,
    staleTime: 1000 * 60 * 5,
  });

  const refreshOverview = () => queryClient.invalidateQueries({ queryKey });

  return {
    overviewData,
    isOverviewFetching,
    overviewError,
    refreshOverview,
  };
};