import { Routes, Route } from "react-router-dom";
import Home from "@/pages/Home";
import SighUp from "@/pages/SignUp"; // create this page

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/signup" element={<SighUp />} />
    </Routes>
  );
}

export default App;
