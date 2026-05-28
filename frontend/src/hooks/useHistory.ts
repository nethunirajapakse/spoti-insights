import { useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import { getHistory, type HistoryResponse } from "@/api/analytics";

export const useHistory = (limit = 20) => {
  const queryClient = useQueryClient();
  const queryKey = ["history", limit];

  const {
    data,
    isFetching: isHistoryFetching,
    isFetchingNextPage,
    fetchNextPage,
    hasNextPage,
    error: historyError,
  } = useInfiniteQuery({
    queryKey,
    queryFn: ({ pageParam }) => getHistory(pageParam, limit),
    initialPageParam: 1,
    getNextPageParam: (lastPage: HistoryResponse) => {
      const loadedSoFar = lastPage.page * lastPage.limit;
      return loadedSoFar < lastPage.total ? lastPage.page + 1 : undefined;
    },
  });

  const historyItems = data?.pages.flatMap((p) => p.items) ?? [];
  const totalCount = data?.pages[0]?.total ?? 0;

  const refreshHistory = () => queryClient.invalidateQueries({ queryKey });

  return {
    historyItems,
    totalCount,
    isHistoryFetching,
    isFetchingNextPage,
    fetchNextPage,
    hasNextPage,
    historyError,
    refreshHistory,
  };
};
