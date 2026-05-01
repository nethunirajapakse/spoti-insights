import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import TopNavbar from "./TopNavbar";

const MainLayout = () => {
  return (
    <div className="min-h-screen bg-[#0e150e] text-[#dde5d9]">
      <Sidebar />
      <main className="ml-64 p-8">
        <TopNavbar />
        <Outlet /> 
      </main>
    </div>
  );
};

export default MainLayout;
