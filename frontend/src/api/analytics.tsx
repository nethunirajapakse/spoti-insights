import api from "@/api/axios";

export const getTopItems = async (time_range: string, limit: number, itemType: string) => {
  const response = await api.get(`/analytics/top-items/${itemType}`, {
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
