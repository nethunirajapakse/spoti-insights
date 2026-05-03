import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getTopItems } from "@/api/analytics";

export const useTopItems = (itemType: string, timeRange: string, limit: number) => {
  const queryClient = useQueryClient();
  const queryKey = ["topItems", itemType, timeRange, limit];

  const {
    data: topItemsData,
    isFetching: isTopItemsFetching,
    error: topItemsError,
  } = useQuery({
    queryKey,
    queryFn: () => getTopItems(timeRange, limit, itemType),
    placeholderData: (previousData) => previousData,
  });

  const refreshTopItems = () => queryClient.invalidateQueries({ queryKey });

  return {
    topItemsData,
    isTopItemsFetching,
    topItemsError,
    refreshTopItems,
  };
};
