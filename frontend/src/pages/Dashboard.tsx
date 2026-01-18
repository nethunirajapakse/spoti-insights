import { useCurrentUser } from "@/hooks/useCurrentUser";

const Dashboard = () => {
  const { data: user } = useCurrentUser();
  
  return (
    <div className="p-10">
      <h1 className="text-3xl font-bold mb-2">
        Welcome, {user?.display_name}!
      </h1>
      <p className="text-gray-500 mb-10">
        Your Spotify ID: {user?.spotify_id}
      </p>

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
