import spotiInsightsLogo from "./assets/logo.png";

function App() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-blue-50 to-blue-100 p-6">
      <div className="flex gap-6 mb-8">
        <img src={spotiInsightsLogo} className="w-20 h-20" alt="Vite logo" />
      </div>
      <h1 className="text-8xl font-bold text-gray-800 mb-6">Spoti Insights</h1>
    </div>
  );
}

export default App;
