import api from "../api/axios";

const SignUpForm = () => {
  const handleSpotifyLogin = async () => {
    try {
      // Fetch the Spotify Auth URL from your backend
      const response = await api.get("/public/auth/spotify/login");
      
      if (response.data.auth_url) {
        // Redirect the whole browser to Spotify
        window.location.href = response.data.auth_url;
      }
    } catch (error) {
      console.error("Failed to initiate login:", error);
      alert("Could not connect to Spotify. Please try again.");
    }
  };

  return (
    <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-10 flex flex-col items-center">
      <h2 className="text-3xl font-bold text-gray-800 mb-2">
        Welcome to Spoti Insights
      </h2>

      <p className="text-gray-600 mb-8 text-center">
        Log in to explore your Spotify listening insights
      </p>

      <button
        onClick={handleSpotifyLogin}
        className="
          flex items-center gap-4
          px-8 py-4
          rounded-full
          bg-[#1DB954]
          text-white
          text-lg
          font-semibold
          hover:bg-[#1ed760]
          transition
          shadow-lg
          w-full
          justify-center
        "
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 168 168"
          className="w-6 h-6 fill-white"
        >
          <path d="M84 0a84 84 0 1 0 0 168A84 84 0 0 0 84 0Zm38.3 121.4a5.2 5.2 0 0 1-7.1 1.7c-19.4-11.9-43.8-14.6-72.5-8a5.2 5.2 0 1 1-2.3-10.1c31.5-7.2 58.9-4.1 80.5 9.2a5.2 5.2 0 0 1 1.7 7Zm10.1-22.6a6.5 6.5 0 0 1-8.9 2.1c-22.2-13.6-56-17.6-82.3-9.6a6.5 6.5 0 1 1-3.8-12.4c30.1-9.1 68.3-4.6 94 11.1a6.5 6.5 0 0 1 2.1 8.8Zm.9-24.1C106.8 58.4 58.6 56.9 36.9 63.6a7.8 7.8 0 0 1-4.6-14.9c25.1-7.7 68.2-6.2 97.8 11.3a7.8 7.8 0 0 1-8 13.2Z" />
        </svg>

        Login with Spotify
      </button>

      <p className="mt-6 text-xs text-gray-500 text-center">
        We only access your listening data.  
        No posts, no messages, ever.
      </p>
    </div>
  );
};

export default SignUpForm;
