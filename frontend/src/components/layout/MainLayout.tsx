import { Outlet } from "react-router-dom";
import Navbar from "@/components/layout/Navbar";

const MainLayout = () => {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main>
        <Outlet /> 
      </main>
    </div>
  );
};

export default MainLayout;
