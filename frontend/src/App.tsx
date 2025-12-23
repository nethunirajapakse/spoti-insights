import { Routes, Route } from "react-router-dom";
import Home from "@/pages/Home";
import SighUp from "@/pages/SignUp"; 
import Dashboard from "@/pages/Dashboard";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/signup" element={<SighUp />} />
      <Route path="/dashboard" element={<Dashboard />} />
    </Routes>
  );
}

export default App;
