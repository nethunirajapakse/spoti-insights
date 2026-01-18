import api from "./axios"; 

export const getSpotifyAuthUrl = async (): Promise<string> => {
  const response = await api.get("/public/auth/spotify/login");
  return response.data.auth_url; 
};

export const getCurrentUser = async () => {
  const response = await api.get("/users/me");
  return response.data;
};

export const logoutUser = async () => {
  await api.post("/public/auth/logout");
};
