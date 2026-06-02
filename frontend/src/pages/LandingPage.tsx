import spotiInsightsLogo from "../assets/logo.png";
import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import Button from "@/components/ui/Button";
import { AlertCircle, Mail, Loader2, CheckCircle2 } from "lucide-react";
import { requestAccess } from "@/api/auth";

const LandingPage = () => {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const error = params.get("error");

  const [inputEmail, setInputEmail] = useState("");
  const [status, setStatus] = useState<
    "idle" | "submitting" | "success" | "error"
  >("idle");
  const [feedbackMsg, setFeedbackMsg] = useState("");

  const handleLoginClick = () => {
    navigate("/signup");
  };

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputEmail.trim()) return;

    setStatus("submitting");
    setFeedbackMsg("");

    try {
      await requestAccess(inputEmail);

      setStatus("success");
      setInputEmail("");
    } catch (err: any) {
      setStatus("error");

      const errorMessage =
        err.response?.data?.detail || "Something went wrong. Please try again.";
      setFeedbackMsg(errorMessage);
    }
  };

  const toastMessages: Record<string, string> = {
    state_missing:
      "Login session expired or cookies were blocked. Please try again.",
    state_mismatch: "Security check failed. Please try logging in again.",
    server_error: "Something went wrong on our end. Please try again shortly.",
  };

  const isAccessDenied = error === "spotify_auth_failed";

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#0b0b0b] text-white p-6 relative overflow-hidden">
      {/* Animated Ambient Background Blobs */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-[#53e076]/10 rounded-full blur-[140px] pointer-events-none animate-float-1" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-[#46bd63]/6 rounded-full blur-[160px] pointer-events-none animate-float-2" />
      <div className="absolute top-[40%] left-[20%] w-[300px] h-[300px] bg-emerald-500/[0.04] rounded-full blur-[120px] pointer-events-none animate-float-2" />

      {error && !isAccessDenied && (
        <div className="absolute top-8 max-w-md w-full mx-auto flex items-start gap-3 bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-2xl animate-in fade-in slide-in-from-top-4 duration-300 z-20">
          <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div className="text-sm font-medium">
            {toastMessages[error] ?? "Login failed. Please try again."}
          </div>
        </div>
      )}

      {isAccessDenied ? (
        <div className="flex flex-col items-center text-center max-w-xl z-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="flex p-4 rounded-3xl bg-amber-400/5 border border-amber-400/20 shadow-2xl shadow-amber-400/5 mb-8 backdrop-blur-md">
            <AlertCircle
              className="w-16 h-16 text-amber-400"
              strokeWidth={1.5}
            />
          </div>

          <h1 className="text-3xl sm:text-4xl font-black text-transparent bg-clip-text bg-gradient-to-b from-white via-zinc-200 to-zinc-500 tracking-tight mb-4">
            Access Not Granted
          </h1>

          <p className="text-zinc-400 text-sm sm:text-base max-w-md font-medium leading-relaxed mb-2">
            Spotify didn't approve access for this account.
          </p>

          <div className="max-w-md text-left p-6 rounded-2xl mt-6 mb-8 backdrop-blur-md border border-white/10 bg-white/[0.02] w-full">
            <p className="text-zinc-300 text-sm leading-relaxed mb-4">
              Per Spotify's Web API policy, apps in development mode can only be
              used by accounts explicitly added to the developer's allowlist
              (limited to 25 users).
            </p>
            <p className="text-zinc-300 text-sm leading-relaxed mb-6">
              This project is currently awaiting formal review. If you'd like to
              test it out, share your Spotify account email below to request
              manual whitelisting.
            </p>

            {/* Email form UI handling submission and delivery feedback loops */}
            {status === "success" ? (
              <div className="flex items-center gap-3 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-xl animate-in fade-in duration-300">
                <CheckCircle2 className="w-5 h-5 shrink-0" />
                <span className="text-sm font-semibold">
                  Request sent! We will add your account shortly.
                </span>
              </div>
            ) : (
              <form onSubmit={handleEmailSubmit} className="space-y-3">
                <div className="relative flex items-center">
                  <Mail className="absolute left-4 w-4 h-4 text-zinc-500" />
                  <input
                    type="email"
                    required
                    disabled={status === "submitting"}
                    placeholder="Enter your Spotify email account"
                    value={inputEmail}
                    onChange={(e) => setInputEmail(e.target.value)}
                    className="w-full bg-black/40 border border-zinc-800 focus:border-[#53e076]/50 focus:ring-1 focus:ring-[#53e076]/50 text-white rounded-xl py-3 pl-11 pr-4 text-sm placeholder-zinc-600 outline-none transition-all disabled:opacity-50"
                  />
                </div>

                <button
                  type="submit"
                  disabled={status === "submitting"}
                  className="w-full flex items-center justify-center gap-2 bg-[#53e076] hover:bg-[#46bd63] disabled:bg-zinc-800 text-black disabled:text-zinc-500 font-semibold text-sm py-3 px-4 rounded-xl transition-colors cursor-pointer disabled:cursor-not-allowed"
                >
                  {status === "submitting" ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Sending Request...
                    </>
                  ) : (
                    "Request Allowlist Access"
                  )}
                </button>

                {status === "error" && (
                  <p className="text-red-400 text-xs mt-1 font-medium pl-1">
                    {feedbackMsg}
                  </p>
                )}
              </form>
            )}
          </div>

          <Button
            label="Back to home"
            onClick={() => navigate("/", { replace: true })}
            className="!bg-white/5 hover:!bg-white/10 !text-zinc-300 hover:!text-white !border !border-white/10 !py-3 !px-8 !text-sm !font-semibold !rounded-xl"
          />
        </div>
      ) : (
        /* Normal landing content */
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
      )}
    </div>
  );
};

export default LandingPage;
