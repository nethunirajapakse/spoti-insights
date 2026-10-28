import { FlaskConical } from "lucide-react";
import { useDemoMode } from "@/hooks/useDemoMode";

/** Shown at the top of every page while demo mode is on. */
const DemoBanner = () => {
  const { isDemo, exitDemo, connectSpotify } = useDemoMode();

  if (!isDemo) return null;

  return (
    <div
      role="status"
      className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-amber-400/20 bg-amber-400/5 px-4 py-3"
    >
      <div className="flex items-center gap-2.5 text-xs leading-relaxed text-amber-100/90 min-w-0">
        <FlaskConical size={16} className="shrink-0 text-amber-300" />
        <span>
          <span className="font-bold text-amber-200">Demo mode.</span> You're
          exploring sample data, not a real Spotify account.
        </span>
      </div>
      <div className="flex items-center gap-2 ml-auto">
        <button
          type="button"
          onClick={connectSpotify}
          className="rounded-full bg-primary px-4 py-1.5 text-[11px] font-bold text-black transition-colors hover:bg-primary-container cursor-pointer"
        >
          Connect Spotify
        </button>
        <button
          type="button"
          onClick={exitDemo}
          className="rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-[11px] font-bold text-zinc-300 transition-colors hover:bg-white/10 hover:text-white cursor-pointer"
        >
          Exit demo
        </button>
      </div>
    </div>
  );
};

export default DemoBanner;
