import { BrowserRouter, Routes, Route } from "react-router-dom";

import TeamPrivateRoute from "./components/TeamPrivateRoute";
import StudentPrivateRoute from "./components/StudentPrivateRoute";
import GuestOnlyRoute from "./components/GuestOnlyRoute";

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
        {/* صفحات عامة — بلا أي حماية، مفتوحة لأي حدا */}
        <Route path="/" element={<GuestOnlyRoute><WelcomePage /></GuestOnlyRoute>} />
        <Route path="/register-step1" element={<GuestOnlyRoute><RegisterStep1Page /></GuestOnlyRoute>} />
        <Route path="/register-step2" element={<GuestOnlyRoute><RegisterStep2Page /></GuestOnlyRoute>} />
        <Route path="/register-step3" element={<GuestOnlyRoute><RegisterStep3Page /></GuestOnlyRoute>} />
        <Route path="/otp" element={<OTP />} />
        <Route path="/academic-guide" element={<AcademicGuide/>}/>
        <Route path="/team-log" element={<TeamLoginPage/>}/>


        {/* صفحات الطالب الشخصية — محتاجة studentCode (بعد تسجيل+تحقق ناجح) */}
        <Route path="/my-card" element={<StudentPrivateRoute><MyCard/></StudentPrivateRoute>}/>
        <Route path="/survey" element={<StudentPrivateRoute><Survey/></StudentPrivateRoute>}/>
        <Route path="/my-points" element={<StudentPrivateRoute><MyPointsPage/></StudentPrivateRoute>}/>


        {/* شاشات مسح فريق العمل — محتاجة تسجيل دخول (JWT) */}
        <Route path="/team-tour" element={<TeamPrivateRoute><TourPage/></TeamPrivateRoute>}/>
        <Route path="/team-college" element={<TeamPrivateRoute><CollegePage/></TeamPrivateRoute>}/>
        <Route path="/team-consultation" element={<TeamPrivateRoute><ConsultationPage/></TeamPrivateRoute>}/>
        <Route path="/team-stadium" element={<TeamPrivateRoute><StadiumPage/></TeamPrivateRoute>}/>


        {/* بوابة الجامعة وإدارة بيانات الطلاب — محتاجة تسجيل دخول (JWT) */}
        <Route path="/gate" element={<TeamPrivateRoute><UniversityGatePage/></TeamPrivateRoute>}/>
        <Route path="/gate-entry-success" element={<TeamPrivateRoute><GateEntrySuccessPage/></TeamPrivateRoute>}/>
        <Route path="/gate-manage" element={<TeamPrivateRoute><StudentDataManagerPage/></TeamPrivateRoute>}/>
        <Route path="/gate-incomplete" element={<TeamPrivateRoute><InWalkIncompletePage/></TeamPrivateRoute>}/>


        {/* لوحة الإدارة العامة — محتاجة تسجيل دخول (JWT) */}
        <Route path="/dashboard" element={<TeamPrivateRoute><GeneralDirectorDashboard/></TeamPrivateRoute>}/>
        <Route path="/create-team-account" element={<TeamPrivateRoute><CreateTeamAccountPage/></TeamPrivateRoute>}/>
        <Route path="/generate-walkin-code" element={<TeamPrivateRoute><GenerateWalkInCodesPage/></TeamPrivateRoute>}/>
      </Routes>
    </BrowserRouter>
  );
}

export default App;