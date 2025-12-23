import { useEffect, useState } from "react";
import api from "../api/axios";
import { useAuthStore } from "../store/useAuthStore";
import { useNavigate } from "react-router-dom";

const Dashboard = () => {
  const { user, setAuth } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUser = async () => {
      try {
        // This request will automatically include the HttpOnly cookie
        const response = await api.get("/users/me"); // Make sure this endpoint exists
        setAuth(response.data);
      } catch (err) {
        console.error("Not authenticated");
        setAuth(null);
        navigate("/"); // Redirect to login if cookie is invalid/missing
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [setAuth, navigate]);

  if (loading) return <div className="p-10">Loading your Spotify data...</div>;

  return (
    <div className="p-10">
      <h1 className="text-2xl font-bold">Welcome, {user?.display_name}!</h1>
      <p>Your Spotify ID: {user?.spotify_id}</p>
      {/* Add your insights components here */}
    </div>
  );
};

export default Dashboard;
