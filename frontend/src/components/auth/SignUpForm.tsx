import { useState } from "react";
import { getSpotifyAuthUrl } from "@/api/auth";
import Button from "@/components/ui/Button";

const SpotifyIcon = ({ className }: { className: string }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 168 168"
    className={`${className} fill-current`}
  >
    <path d="M84 0a84 84 0 1 0 0 168A84 84 0 0 0 84 0Zm38.3 121.4a5.2 5.2 0 0 1-7.1 1.7c-19.4-11.9-43.8-14.6-72.5-8a5.2 5.2 0 1 1-2.3-10.1c31.5-7.2 58.9-4.1 80.5 9.2a5.2 5.2 0 0 1 1.7 7Zm10.1-22.6a6.5 6.5 0 0 1-8.9 2.1c-22.2-13.6-56-17.6-82.3-9.6a6.5 6.5 0 1 1-3.8-12.4c30.1-9.1 68.3-4.6 94 11.1a6.5 6.5 0 0 1 2.1 8.8Zm.9-24.1C106.8 58.4 58.6 56.9 36.9 63.6a7.8 7.8 0 0 1-4.6-14.9c25.1-7.7 68.2-6.2 97.8 11.3a7.8 7.8 0 0 1-8 13.2Z" />
  </svg>
);

const SignUpForm = () => {
  const [isLoading, setIsLoading] = useState(false);

  const handleSpotifyLogin = async () => {
    setIsLoading(true);
    try {
      const authUrl = await getSpotifyAuthUrl();
      if (authUrl) {
        globalThis.location.href = authUrl;
      } else {
        alert("No auth URL returned.");
        setIsLoading(false);
      }
    } catch (error) {
      console.error(error);
      setIsLoading(false);
    }
  };

  return (
    /* Glassmorphism Classes Applied Below */
    <div className="w-full max-w-md bg-white/[0.02] border border-white/10 rounded-3xl shadow-[0_25px_50px_-12px_rgba(0,0,0,0.7)] p-10 flex flex-col items-center backdrop-blur-md z-10">
      <header className="text-center mb-8">
        <h2 className="text-2xl sm:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-b from-white to-zinc-400 tracking-tight mb-2">
          Welcome to Spoti Insights
        </h2>
        <p className="text-sm text-zinc-400 font-medium leading-relaxed">
          Log in to explore your Spotify listening insights
        </p>
      </header>

      <Button
        label="Login with Spotify"
        Icon={SpotifyIcon}
        onClick={handleSpotifyLogin}
        isLoading={isLoading}
        className="!w-full !bg-[#53e076] hover:!bg-[#46bd63] !text-black !font-bold !py-4.5 !text-base !rounded-full shadow-lg shadow-[#53e076]/20 transition-all hover:scale-[1.01] active:scale-[0.99]"
      />

      <footer className="mt-8 pt-4 border-t border-white/5 w-full">
        <p className="text-[11px] text-zinc-500 text-center font-medium leading-normal px-2">
          We only access your listening data. <br />No posts, no messages, ever.
        </p>
      </footer>
    </div>
  );
};

export default SignUpForm;
