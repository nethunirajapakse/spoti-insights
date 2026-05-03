import api from "@/api/axios";

export const getTopTracks = async (time_range: string, limit: number) => {
  const response = await api.get("/analytics/top-items/tracks", {
    params: { time_range, limit },
  });
  return response.data;
};

export const getRecentlyPlayed = async (limit: number) => {
  const response = await api.get("/analytics/recently-played", {
    params: { limit },
  });
  return response.data;
};

export const getUserPlaylists = async (limit: number, offset: number) => {
  const response = await api.get("/analytics/playlists", {
    params: { limit, offset },
  });
  return response.data;
};
