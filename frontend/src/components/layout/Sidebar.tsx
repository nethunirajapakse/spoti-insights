import { NavLink } from "react-router-dom";
import { 
  History, 
  LayoutDashboard, 
  Music2, 
  Settings, 
  Sparkles,
  HelpCircle
} from 'lucide-react';

const Sidebar = () => {
  const navItems = [
    { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { name: "History", path: "/history", icon: History },
    { name: "Playlists", path: "/playlists", icon: Music2 },
  ];

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-[#091009]/60 backdrop-blur-2xl border-r border-white/10 z-40 flex flex-col">
      {/* Brand Logo */}
      <div className="p-8">
        <h1 className="text-2xl font-black text-primary tracking-tighter italic">
          Spoti-Insights
        </h1>
        <p className="text-[10px] uppercase tracking-[0.2em] text-outline font-bold mt-1">
          Premium Analyst
        </p>
      </div>
      
      {/* Main Navigation */}
      <nav className="flex-1 px-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex w-full items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 group ${
                isActive 
                  ? "bg-white/5 text-primary font-bold shadow-lg shadow-black/20 relative before:absolute before:left-0 before:w-1 before:h-6 before:bg-primary before:rounded-full" 
                  : "text-on-surface-variant hover:bg-white/5 hover:text-white"
              }`
            }
          >
            <item.icon size={20} className="group-hover:scale-110 transition-transform" />
            <span className="text-sm font-medium tracking-tight">{item.name}</span>
          </NavLink>
        ))}
      </nav>

      {/* Action Section */}
      <div className="p-4 px-6">
        <button className="w-full bg-primary-container hover:bg-primary transition-colors text-on-primary-container font-bold py-3 rounded-full flex items-center justify-center gap-2 text-sm shadow-lg shadow-primary/10 active:scale-95 duration-200">
          <Sparkles size={16} />
          Generate Report
        </button>
      </div>

      {/* Footer Navigation */}
      <div className="p-4 border-t border-white/5 space-y-1">
        {/* Help Link Added Here */}
        <NavLink 
          to="/help" 
          className="flex items-center gap-4 px-4 py-2 text-outline hover:text-white transition-colors text-sm"
        >
          <HelpCircle size={18} />
          Help & Support
        </NavLink>

        <NavLink 
          to="/settings" 
          className="flex items-center gap-4 px-4 py-2 text-outline hover:text-white transition-colors text-sm"
        >
          <Settings size={18} />
          Settings
        </NavLink>
      </div>
    </aside>
  );
};

export default Sidebar;
