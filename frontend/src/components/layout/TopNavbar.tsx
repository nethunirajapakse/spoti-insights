import { useLocation } from "react-router-dom";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { useLogout } from "@/hooks/useLogout";
import Button from "@/components/ui/Button";
import { LogOut, Search } from "lucide-react";

const TopNavbar = () => {
  const { data: user } = useCurrentUser();
  const { mutate: handleLogout, isPending } = useLogout();
  const location = useLocation();

  // Map paths to titles
  const getTitle = (path: string) => {
    switch (path) {
      case '/dashboard': return 'Artist Insights';
      case '/history': return 'Listening History';
      case '/settings': return 'Settings';
      default: return 'Overview';
    }
  };

  return (
    <header className="flex items-center justify-between mb-8">
      <div>
        <h2 className="text-xl font-black text-[#53e076] uppercase tracking-wider">
          {getTitle(location.pathname)}
        </h2>
        <p className="text-[10px] text-[#bccbb9] font-medium uppercase tracking-tighter">
          Spoti-Insights / {location.pathname.replace('/', '')}
        </p>
      </div>
      
      <div className="flex items-center gap-6">
        <div className="relative hidden md:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#bccbb9]" size={16} />
          <input 
            type="text" 
            placeholder="Search insights..." 
            className="bg-white/5 border border-white/10 rounded-full py-1.5 pl-10 pr-4 text-sm focus:outline-none focus:border-[#53e076]/50 transition-colors"
          />
        </div>

        <div className="flex items-center gap-3 pr-4 border-r border-white/10">
          <span className="text-sm font-medium">{user?.display_name || "User"}</span>
          <img 
            src={user?.images?.[0]?.url} 
            className="w-8 h-8 rounded-full border border-[#53e076]/30 shadow-lg shadow-[#53e076]/10" 
            alt="avatar" 
          />
        </div>

        <Button
          label="Logout"
          Icon={LogOut}
          variant="danger"
          isLoading={isPending}
          onClick={() => handleLogout()}
          className="!py-2 !px-4 !text-sm"
        />
      </div>
    </header>
  );
};

export default TopNavbar;
