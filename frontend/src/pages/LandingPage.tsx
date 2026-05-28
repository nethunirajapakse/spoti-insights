import spotiInsightsLogo from "../assets/logo.png";
import { useNavigate, useSearchParams } from "react-router-dom";
import Button from "@/components/ui/Button";
import { AlertCircle } from "lucide-react";

const LandingPage = () => {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const error = params.get("error");

  const handleLoginClick = () => {
    navigate("/signup");
  };

  const errorMessages: Record<string, string> = {
    state_missing:
      "Login session expired or cookies were blocked. Please try again.",
    state_mismatch: "Security check failed. Please try logging in again.",
    spotify_auth_failed: "Spotify login was declined. Please try again.",
    server_error: "Something went wrong on our end. Please try again shortly.",
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#0b0b0b] text-white p-6 relative overflow-hidden">

      {/* Animated Ambient Background Blobs */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-[#53e076]/10 rounded-full blur-[140px] pointer-events-none animate-float-1" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-[#46bd63]/6 rounded-full blur-[160px] pointer-events-none animate-float-2" />
      <div className="absolute top-[40%] left-[20%] w-[300px] h-[300px] bg-emerald-500/[0.04] rounded-full blur-[120px] pointer-events-none animate-float-2" />

      {/* Error Callout */}
      {error && (
        <div className="absolute top-8 max-w-md w-full mx-auto flex items-start gap-3 bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-2xl animate-in fade-in slide-in-from-top-4 duration-300 z-20">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div className="text-sm font-medium">
            {errorMessages[error] ?? "Login failed. Please try again."}
          </div>
        </div>
      )}

      {/* Content Card Wrapper - Hover classes removed from here */}
      <div className="flex flex-col items-center text-center max-w-xl z-10">
        <div className="flex p-4 rounded-3xl bg-white/5 border border-white/15 shadow-2xl shadow-[#53e076]/5 mb-8 backdrop-blur-md">
          <img
            src={spotiInsightsLogo}
            className="w-16 h-16 object-contain"
            alt="Spoti Insights logo"
          />
        </div>

        <h1 className="text-5xl sm:text-7xl font-black text-transparent bg-clip-text bg-gradient-to-b from-white via-zinc-200 to-zinc-500 tracking-tighter mb-4">
          Spoti Insights
        </h1>

        <p className="text-zinc-400 text-base sm:text-lg max-w-sm font-medium leading-relaxed mb-8">
          Deep dive into your listening habits, playlists trends, and
          personalized audio metrics.
        </p>

        <Button
          label="Connect with Spotify"
          onClick={handleLoginClick}
          className="!bg-[#53e076]/5 hover:!bg-[#53e076]/10 !text-green-300 hover:!text-[#53e076] !border !border-[#53e076]/20 hover:!border-[#53e076]/40 !py-3.5 !px-10 !text-sm !font-semibold !rounded-xl transition-all duration-300 shadow-xl shadow-black/40 hover:scale-[1.01] active:scale-[0.99]"
        />
      </div>
    </div>
  );
};

export default LandingPage;
