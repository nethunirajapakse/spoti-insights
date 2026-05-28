import { useState, useEffect } from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  History,
  LayoutDashboard,
  Music2,
  Settings,
  HelpCircle,
  Menu,
  X,
} from "lucide-react";

const navItems = [
  { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
  { name: "History", path: "/history", icon: History },
  { name: "Playlists", path: "/playlists", icon: Music2 },
];

const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  // Auto-close on route change (mobile)
  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  // Lock body scroll when the drawer is open on mobile
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  return (
    <>
      {/* Mobile hamburger — only shown when drawer is closed, sits above content */}
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        aria-label="Open menu"
        className={`lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-white/5 backdrop-blur-xl border border-white/10 text-white ${
          isOpen ? "hidden" : ""
        }`}
      >
        <Menu size={20} />
      </button>

      {/* Backdrop — only on mobile when open */}
      {isOpen && (
        <button
          type="button"
          onClick={() => setIsOpen(false)}
          aria-label="Close menu"
          className="lg:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
        />
      )}

      {/* The sidebar itself: always visible on lg+, slide-in on mobile */}
      <aside
        className={`fixed left-0 top-0 h-full w-64 bg-[#091009]/80 backdrop-blur-2xl border-r border-white/10 z-40 flex flex-col transition-transform duration-300 ease-out
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
          lg:translate-x-0
        `}
      >
        {/* Brand + mobile close button */}
        <div className="p-8 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-black text-primary tracking-tighter italic">
              Spoti-Insights
            </h1>
            <p className="text-[9px] uppercase tracking-[0.25em] text-outline font-black mt-1">
              Advanced Analytics
            </p>
          </div>
          <button
            type="button"
            onClick={() => setIsOpen(false)}
            aria-label="Close menu"
            className="lg:hidden text-on-surface-variant hover:text-white"
          >
            <X size={20} />
          </button>
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
              <item.icon
                size={20}
                className="group-hover:scale-110 transition-transform"
              />
              <span className="text-sm font-medium tracking-tight">
                {item.name}
              </span>
            </NavLink>
          ))}
        </nav>

        {/* Footer Navigation */}
        <div className="p-4 border-t border-white/5 space-y-1">
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
    </>
  );
};

export default Sidebar;
