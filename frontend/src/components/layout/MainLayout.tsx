import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import TopNavbar from "./TopNavbar";

const MainLayout = () => {
  return (
    <div className="min-h-screen">
      <Sidebar />
      <main className="ml-64 p-gutter">
        <TopNavbar />
        <Outlet />
      </main>
    </div>
  );
};

export default MainLayout;
