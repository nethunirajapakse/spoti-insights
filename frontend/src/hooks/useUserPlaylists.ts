import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getUserPlaylists } from "@/api/analytics";

export const useUserPlaylists = (limit: number, offset: number) => {
  const queryClient = useQueryClient();
  const queryKey = ["userPlaylists", limit, offset];

  const {
    data: playlistsData,
    isFetching: isPlaylistsFetching,
    error: playlistsError,
  } = useQuery({
    queryKey,
    queryFn: () => getUserPlaylists(limit, offset),
    placeholderData: (previousData) => previousData,
  });

  const refreshPlaylists = () => queryClient.invalidateQueries({ queryKey });

  return {
    playlistsData,
    isPlaylistsFetching,
    playlistsError,
    refreshPlaylists,
  };
};
