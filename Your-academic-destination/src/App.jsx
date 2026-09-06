import { BrowserRouter, Routes, Route } from "react-router-dom";

import WelcomePage from "./pages/student/WelcomePage";
import RegisterStep1Page from "./pages/student/RegisterStep1Page";
import RegisterStep2Page from "./pages/student/RegisterStep2Page";
import RegisterStep3Page from "./pages/student/RegisterStep3Page";
import OTP from "./pages/student/OTP";


import MyCard from "./pages/student/MyCard";
import AcademicGuide from "./pages/student/AcademicGuide";
import Survey from "./pages/student/Survey";
import MyPointsPage from "./pages/student/MyPointsPage";


import TeamLoginPage from "./pages/scanners/TeamLoginPage";
import TourPage from "./pages/scanners/TourPage";
import CollegePage from "./pages/scanners/CollegePage";
import StadiumPage from "./pages/scanners/StadiumPage";
import ConsultationPage from "./pages/scanners/ConsultationPage";



import UniversityGatePage from "./pages/UniGate/UniversityGatePage";
import GateEntrySuccessPage from "./pages/UniGate/GateEntrySuccessPage";
import StudentDataManagerPage from "./pages/UniGate/StudentDataManagerPage"
import InWalkIncompletePage from "./pages/UniGate/InWalkIncompletePage";



import GeneralDirectorDashboard from "./pages/Admin/GeneralDirectorDashboard";
import CreateTeamAccountPage from "./pages/Admin/CreateTeamAccountPage";
import GenerateWalkInCodesPage from "./pages/Admin/GenerateWalkInCodesPage";



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
        <Route path="/my-points" element={<MyPointsPage/>}/>


        <Route path="/team-log" element={<TeamLoginPage/>}/>
        <Route path="/team-tour" element={<TourPage/>}/>
        <Route path="/team-college" element={<CollegePage/>}/>
        <Route path="/team-consultation" element={<ConsultationPage/>}/>
        <Route path="/team-stadium" element={<StadiumPage/>}/>


        <Route path="/gate" element={<UniversityGatePage/>}/>
        <Route path="/gate-entry-success" element={<GateEntrySuccessPage/>}/>
        <Route path="/gate-manage" element={<StudentDataManagerPage/>}/>
        <Route path="/gate-incomplete" element={<InWalkIncompletePage/>}/>


        <Route path="/dashboard" element={<GeneralDirectorDashboard/>}/>
        <Route path="/create-team-account" element={<CreateTeamAccountPage/>}/>
        <Route path="/generate-walkin-code" element={<GenerateWalkInCodesPage/>}/>
      </Routes>
    </BrowserRouter>
  );
}

export default App;