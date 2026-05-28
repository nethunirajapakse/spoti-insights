import { useInfiniteQuery, useQueryClient } from "@tanstack/react-query";
import { getUserPlaylists } from "@/api/analytics";

export const useUserPlaylists = (limit = 20) => {
  const queryClient = useQueryClient();
  const queryKey = ["userPlaylists", limit];

  const {
    data,
    isFetching: isPlaylistsFetching,
    isFetchingNextPage,
    fetchNextPage,
    hasNextPage,
    error: playlistsError,
  } = useInfiniteQuery({
    queryKey,
    queryFn: ({ pageParam = 0 }) => getUserPlaylists(limit, pageParam),
    initialPageParam: 0,
    getNextPageParam: (lastPage) => {
      if (!lastPage?.next) return undefined;
      const currentOffset = lastPage.offset ?? 0;
      const totalLoaded = currentOffset + lastPage.items.length;
      return totalLoaded < lastPage.total ? totalLoaded : undefined;
    },
  });

  const playlistsItems = data?.pages.flatMap((page) => page.items) ?? [];
  const totalCount = data?.pages[0]?.total ?? 0;

  const refreshPlaylists = () => queryClient.invalidateQueries({ queryKey });

  return {
    playlistsItems,
    totalCount,
    isPlaylistsFetching,
    isFetchingNextPage,
    fetchNextPage,
    hasNextPage,
    playlistsError,
    refreshPlaylists,
  };
};
