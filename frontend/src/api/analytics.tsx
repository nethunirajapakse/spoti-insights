import api from "@/api/axios";

export const getTopTracks = async (timeRange = "medium_term", limit = 10) => {
  const response = await api.get("/analytics/top-items/tracks", {
    params: {
      time_range: timeRange,
      limit: limit,
    },
  });
  return response.data;
};