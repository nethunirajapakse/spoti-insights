import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getHourlyVelocity } from "@/api/analytics";

export const useHourlyVelocity = () => {
  const queryClient = useQueryClient();
  const queryKey = ["hourlyVelocity"];

  const {
    data: hourlyVelocityData,
    isFetching: isHourlyVelocityFetching,
    error: hourlyVelocityError,
  } = useQuery({
    queryKey,
    queryFn: getHourlyVelocity,
    placeholderData: (previousData) => previousData,
    staleTime: 1000 * 60 * 2,
  });

  const refreshHourlyVelocity = () =>
    queryClient.invalidateQueries({ queryKey });

  return {
    hourlyVelocityData,
    isHourlyVelocityFetching,
    hourlyVelocityError,
    refreshHourlyVelocity,
  };
};
