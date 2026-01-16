import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/store/useAuthStore";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { useLogout } from "@/hooks/useLogout";
import Button from "@/components/ui/Button";

const Dashboard = () => {
  const navigate = useNavigate();
  const { user, setAuth } = useAuthStore();

  const { data, isLoading, isError } = useCurrentUser();
  const { mutate: handleLogout, isPending: isLoggingOut } = useLogout();

  useEffect(() => {
    if (data) {
      setAuth(data);
    } else if (isError) {
      setAuth(null);
      navigate("/");
    }
  }, [data, isError, setAuth, navigate]);

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
          <h1 className="text-3xl font-bold">
            Welcome, {user?.display_name}!
          </h1>
          <p className="text-gray-500">
            Your Spotify ID: {user?.spotify_id}
          </p>
        </div>

        <Button
          label="Log Out"
          variant="danger"
          isLoading={isLoggingOut}
          onClick={handleLogout}
        />
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
