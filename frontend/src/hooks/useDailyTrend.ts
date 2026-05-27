import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getDailyTrend } from "@/api/analytics";

export const useDailyTrend = (days = 30) => {
  const queryClient = useQueryClient();
  const queryKey = ["dailyTrend", days];

  const {
    data: dailyTrendData,
    isFetching: isDailyTrendFetching,
    error: dailyTrendError,
  } = useQuery({
    queryKey,
    queryFn: () => getDailyTrend(days),
    placeholderData: (previousData) => previousData,
    staleTime: 1000 * 60 * 5,
  });

  const refreshDailyTrend = () => queryClient.invalidateQueries({ queryKey });

  return {
    dailyTrendData,
    isDailyTrendFetching,
    dailyTrendError,
    refreshDailyTrend,
  };
};
