import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import TopNavbar from "./TopNavbar";

const MainLayout = () => {
  return (
    <div className="min-h-screen">
      <Sidebar />
      <main className="lg:ml-64 p-gutter pt-16 lg:pt-gutter">
        <TopNavbar />
        <Outlet />
      </main>
    </div>
  );
};

export default MainLayout;
