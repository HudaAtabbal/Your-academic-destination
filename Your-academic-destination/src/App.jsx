import { BrowserRouter, Routes, Route } from "react-router-dom";

import WelcomePage from "./pages/WelcomePage";
import RegisterStep1Page from "./pages/RegisterStep1Page";
import RegisterStep2Page from "./pages/RegisterStep2Page";
import OTP from "./pages/OTP";

import MyCard from "./pages/MyCard";


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<WelcomePage />} />
        <Route path="/register-step1" element={<RegisterStep1Page />} />
        <Route path="/register-step2" element={<RegisterStep2Page />} />
        <Route path="/otp" element={<OTP />} />
        <Route path="/my-card" element={<MyCard/>}/>
      </Routes>
    </BrowserRouter>
  );
}

export default App;