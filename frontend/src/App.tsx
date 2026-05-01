// App.tsx
import { Routes, Route } from "react-router-dom";
import LandingPage from "@/pages/LandingPage";
import SignUp from "@/pages/SignUp"; 
import Dashboard from "@/pages/Dashboard";
import History from "@/pages/History";
import MainLayout from "@/components/layout/MainLayout";
import ProtectedRoute from "@/components/auth/ProtectedRoute";

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/signup" element={<SignUp />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/history" element={<History />} />
        </Route>
      </Route>
    </Routes>
  );
}

export default App;
