import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getTodaySummary } from "@/api/analytics";

export const useTodaySummary = () => {
  const queryClient = useQueryClient();
  const queryKey = ["todaySummary"];

  const {
    data: todaySummaryData,
    isFetching: isTodaySummaryFetching,
    error: todaySummaryError,
  } = useQuery({
    queryKey,
    queryFn: getTodaySummary,
    placeholderData: (previousData) => previousData,
    staleTime: 1000 * 60 * 2,
  });

  const refreshTodaySummary = () => queryClient.invalidateQueries({ queryKey });

  return {
    todaySummaryData,
    isTodaySummaryFetching,
    todaySummaryError,
    refreshTodaySummary,
  };
};