import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/useAuthStore";
import { logoutUser } from "@/api/auth";

export const useLogout = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { logout } = useAuthStore();

  return useMutation({
    mutationFn: logoutUser,
    onSuccess: () => {
      logout();
      queryClient.clear();
      navigate("/");
    },
    onError: (error) => {
      console.error("Logout failed:", error);
      logout();
      navigate("/");
    },
  });
};
