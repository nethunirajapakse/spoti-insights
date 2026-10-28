import api from "@/api/axios";
import { isDemoMode, useDemoStore } from "@/store/useDemoStore";
import { demoCurrentUser } from "@/demo/demoApi";

export const getSpotifyAuthUrl = async (): Promise<string> => {
  const response = await api.get("/public/auth/spotify/login");
  return response.data.auth_url;
};

export const getCurrentUser = async () => {
  if (isDemoMode()) return demoCurrentUser();
  const response = await api.get("/users/me");
  return response.data;
};

export const logoutUser = async () => {
  if (isDemoMode()) {
    // Nothing to invalidate on the server; just leave demo mode.
    useDemoStore.getState().disable();
    return;
  }
  await api.post("/public/auth/logout");
};

export const requestAccess = async (emailAddress: string) => {
  await api.post("/request-access", { email: emailAddress });
};
