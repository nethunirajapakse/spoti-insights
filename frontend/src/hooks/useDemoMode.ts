import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useDemoStore } from "@/store/useDemoStore";

/**
 * Entry and exit points for demo mode.
 *
 * Cached queries are cleared on every switch so sample data never leaks into a
 * real session (or the other way around).
 */
export const useDemoMode = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const isDemo = useDemoStore((s) => s.isDemo);
  const enable = useDemoStore((s) => s.enable);
  const disable = useDemoStore((s) => s.disable);

  const startDemo = () => {
    enable();
    queryClient.clear();
    navigate("/dashboard");
  };

  const exitDemo = () => {
    disable();
    queryClient.clear();
    navigate("/", { replace: true });
  };

  /** Leave demo mode and head to the real Spotify login. */
  const connectSpotify = () => {
    disable();
    queryClient.clear();
    navigate("/signup");
  };

  return { isDemo, startDemo, exitDemo, connectSpotify };
};
