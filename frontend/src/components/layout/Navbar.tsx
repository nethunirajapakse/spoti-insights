
import { NavLink } from "react-router-dom";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import { useLogout } from "@/hooks/useLogout";
import Button from "@/components/ui/Button";

const Navbar = () => {
  const { data: user } = useCurrentUser();
  const { mutate: handleLogout, isPending } = useLogout();

  const navItems = [
    { name: "Dashboard", path: "/dashboard" },
  ];

  return (
    <nav className="bg-black text-white px-6 py-4 flex justify-between items-center">
      <div className="flex items-center space-x-6">
        <span className="text-xl font-bold">Spoti Insights</span>
        
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              isActive ? "text-purple-400 font-semibold" : "hover:text-gray-300"
            }
          >
            {item.name}
          </NavLink>
        ))}
      </div>

      <div className="flex items-center space-x-4">
        <span className="text-gray-400 hidden sm:block">
          {user?.display_name}
        </span>
        <Button
          label="Logout"
          variant="danger"
          isLoading={isPending}
          onClick={() => handleLogout()}
        />
      </div>
    </nav>
  );
};

export default Navbar;