import { useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/useAuthStore";
import { getCurrentUser, logoutUser } from "@/api/index.tsx";

const Dashboard = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, setAuth, logout } = useAuthStore();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["currentUser"],
    queryFn: getCurrentUser,
    retry: false,
  });

  useEffect(() => {
    if (data) {
      setAuth(data);
    } else if (isError) {
      setAuth(null);
      navigate("/");
    }
  }, [data, isError, setAuth, navigate]);

  const { mutate: handleLogout, isPending: isLoggingOut } = useMutation({
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

  if (isLoading || isLoggingOut) {
    return (
      <div className="p-10 text-white bg-black h-screen">
        Loading your Spotify data...
      </div>
    );
  }

  return (
    <div className="p-10 relative">
      <div className="flex justify-between items-center mb-10">
        <div>
          <h1 className="text-3xl font-bold">Welcome, {user?.display_name}!</h1>
          <p className="text-gray-500">Your Spotify ID: {user?.spotify_id}</p>
        </div>

        <button
          onClick={() => handleLogout()}
          disabled={isLoggingOut}
          className="px-6 py-2 bg-red-500 hover:bg-red-600 text-white font-semibold rounded-full transition duration-200 shadow-md disabled:opacity-50"
        >
          {isLoggingOut ? "Logging out..." : "Log Out"}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 bg-gray-100 rounded-xl">
          <p className="italic text-gray-600">
            Your listening insights are loading...
          </p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
