import { BrowserRouter, Routes, Route } from "react-router-dom";

import WelcomePage from "./pages/WelcomePage";
import RegisterStep1Page from "./pages/RegisterStep1Page";
import RegisterStep2Page from "./pages/RegisterStep2Page";
import RegisterStep3Page from "./pages/RegisterStep3Page";
import OTP from "./pages/OTP";

import MyCard from "./pages/MyCard";
import AcademicGuide from "./pages/AcademicGuide";
import Survey from "./pages/Survey";


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<WelcomePage />} />
        <Route path="/register-step1" element={<RegisterStep1Page />} />
        <Route path="/register-step2" element={<RegisterStep2Page />} />
        <Route path="/register-step3" element={<RegisterStep3Page />} />
        <Route path="/otp" element={<OTP />} />
        <Route path="/my-card" element={<MyCard/>}/>
        <Route path="/academic-guide" element={<AcademicGuide/>}/>
        <Route path="/survey" element={<Survey/>}/>
      </Routes>
    </BrowserRouter>
  );
}

export default App;