import { BrowserRouter, Routes, Route } from "react-router-dom";

import WelcomePage from "./pages/student/WelcomePage";
import RegisterStep1Page from "./pages/student/RegisterStep1Page";
import RegisterStep2Page from "./pages/student/RegisterStep2Page";
import RegisterStep3Page from "./pages/student/RegisterStep3Page";
import OTP from "./pages/student/OTP";

import MyCard from "./pages/student/MyCard";
import AcademicGuide from "./pages/student/AcademicGuide";
import Survey from "./pages/student/Survey";



import TeamLoginPage from "./pages/scanners/TeamLoginPage";
import TourPage from "./pages/scanners/TourPage";
import CollegePage from "./pages/scanners/CollegePage";
import StadiumPage from "./pages/scanners/StadiumPage";
import ConsultationPage from "./pages/scanners/ConsultationPage";



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


        <Route path="/team-log" element={<TeamLoginPage/>}/>
        <Route path="/team-tour" element={<TourPage/>}/>
        <Route path="/team-college" element={<CollegePage/>}/>
        <Route path="/team-consultation" element={<ConsultationPage/>}/>
        <Route path="/team-stadium" element={<StadiumPage/>}/>
      </Routes>
    </BrowserRouter>
  );
}

export default App;