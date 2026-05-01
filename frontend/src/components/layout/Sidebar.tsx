import { NavLink } from "react-router-dom";
import { BarChart3, History } from 'lucide-react';

const Sidebar = () => {
  const navItems = [
    { name: "Artist Insights", path: "/dashboard", icon: BarChart3 },
    { name: "Listening History", path: "/history", icon: History },
  ];

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-[#1a211a]/40 backdrop-blur-xl border-r border-white/10 z-40 flex flex-col">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-[#53e076]">Spoti-Insights</h1>
      </div>
      
      <nav className="flex-1 px-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex w-full items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                isActive 
                  ? "bg-[#53e076]/10 text-[#53e076] font-bold border-l-4 border-[#53e076]" 
                  : "text-[#bccbb9] hover:bg-white/5"
              }`
            }
          >
            <item.icon size={20} />
            <span>{item.name}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
