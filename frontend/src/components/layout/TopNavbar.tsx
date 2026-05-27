import { useState, useRef, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { useLogout } from "@/hooks/useLogout";
import Button from "@/components/ui/Button";

const TITLES: Record<string, string> = {
  "/dashboard": "Overview",
  "/history": "Recently Played",
  "/playlists": "Your Library",
  "/settings": "Settings",
};

const TopNavbar = () => {
  const { data: user } = useCurrentUser();
  const { mutate: handleLogout, isPending } = useLogout();
  const location = useLocation();
  const title = TITLES[location.pathname] ?? "Overview";

  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target;
      // Narrow with `instanceof Node` instead of asserting — Sonar flagged the
      // `as Node` cast as unnecessary, and this is the type-safe equivalent.
      if (
        target instanceof Node &&
        menuRef.current &&
        !menuRef.current.contains(target)
      ) {
        setIsMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <header className="flex items-center justify-between mb-8 gap-4 relative">
      {/* Title */}
      <div className="ml-12 lg:ml-0 min-w-0">
        <h2 className="text-lg sm:text-xl font-black text-[#53e076] uppercase tracking-wider truncate">
          {title}
        </h2>
        <p className="hidden sm:block text-[10px] text-[#bccbb9] font-medium uppercase tracking-tighter">
          Spoti-Insights / {location.pathname.replace("/", "")}
        </p>
      </div>

      {/* User Profile Trigger */}
      <div className="relative" ref={menuRef}>
        <button
          type="button"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          className="flex items-center gap-2 p-1 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 transition-all focus:outline-none group"
        >
          {user?.images?.[0]?.url ? (
            <img
              src={user.images[0].url}
              className="w-8 h-8 rounded-full border border-[#53e076]/20 group-hover:border-[#53e076]/60 transition-colors"
              alt="avatar"
            />
          ) : (
            <div className="w-8 h-8 rounded-full border border-[#53e076]/20 bg-zinc-800 flex items-center justify-center text-xs font-bold text-[#53e076] group-hover:border-[#53e076]/60 transition-colors">
              {(user?.display_name || "U").charAt(0).toUpperCase()}
            </div>
          )}
        </button>

        {/* Account Menu */}
        {isMenuOpen && (
          <div className="absolute right-0 mt-3 w-72 bg-[#121212] border border-white/10 rounded-3xl shadow-2xl p-5 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
            {/* Header: Identity Section */}
            <div className="flex flex-col items-center text-center mb-5 mt-2">
              {user?.images?.[0]?.url ? (
                <img
                  src={user.images[0].url}
                  className="w-16 h-16 rounded-full border-2 border-[#53e076]/30 mb-3"
                  alt="avatar"
                />
              ) : (
                <div className="w-16 h-16 rounded-full bg-zinc-800 border-2 border-[#53e076]/20 flex items-center justify-center text-xl font-black text-[#53e076] mb-3 shadow-lg tracking-wider">
                  {(user?.display_name || "U").charAt(0).toUpperCase()}
                </div>
              )}
              <h3 className="text-base font-bold text-zinc-100 tracking-tight leading-tight">
                {user?.display_name || "Nethuni Rajapakse"}
              </h3>
              <p className="text-xs text-zinc-400 mt-0.5 truncate max-w-full px-2">
                {user?.email || "user@gmail.com"}
              </p>
            </div>

            {/* Action Buttons Stack */}
            <div className="flex flex-col gap-2">
              <Button
                label="Sign out"
                variant="secondary"
                isLoading={isPending}
                onClick={() => {
                  setIsMenuOpen(false);
                  handleLogout();
                }}
                className="!w-full !bg-transparent hover:!bg-red-500/10 !text-zinc-300 hover:!text-red-400 !border !border-white/10 hover:!border-red-500/20 !shadow-none !py-3 !px-4 !text-sm !font-medium transition-colors"
              />
            </div>
          </div>
        )}
      </div>
    </header>
  );
};

export default TopNavbar;
