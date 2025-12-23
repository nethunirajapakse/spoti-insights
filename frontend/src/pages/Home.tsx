import spotiInsightsLogo from "../assets/logo.png";
import { useNavigate } from "react-router-dom";

const Home = () => {
  const navigate = useNavigate();

  const handleLoginClick = () => {
    navigate("/signup");
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-blue-50 to-blue-100 p-6">
      <div className="flex gap-6 mb-8">
        <img
          src={spotiInsightsLogo}
          className="w-20 h-20"
          alt="Spoti Insights logo"
        />
      </div>
      <h1 className="text-8xl font-bold text-gray-800 mb-6">Spoti Insights</h1>

      <button
        onClick={handleLoginClick}
        className="mt-6 px-8 py-3 rounded-xl bg-blue-600 text-white text-lg font-semibold hover:bg-blue-700 transition duration-300 shadow-md"
      >
        Login
      </button>
    </div>
  );
};

export default Home;
