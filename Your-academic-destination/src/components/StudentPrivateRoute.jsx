import React from 'react';
import { Navigate } from 'react-router-dom';

/**
 * StudentPrivateRoute — بوابة حماية لصفحات الطالب الشخصية (البطاقة، الاستبيان،
 * النقاط، الدليل الأكاديمي). لازم يكون عند الطالب studentCode **و** studentName
 * معاً — يعني خلّص تسجيل + تحقق OTP فعلاً، أو استرجع بطاقته من FindCardPage.
 * وجود studentName مع studentCode دليل على اكتمال التحقق (بينكتب studentCode
 * الرسمي بس بعد نجاح OTP). أي محاولة فتح مباشرة بدون هيك بترجع لصفحة البداية.
 *
 * الاستخدام بـ App.jsx:
 *   <Route path="/my-card" element={<StudentPrivateRoute><MyCard/></StudentPrivateRoute>} />
 */
const StudentPrivateRoute = ({ children }) => {
  const studentCode = localStorage.getItem('studentCode');
  const studentName = localStorage.getItem('studentName');

  if (!studentCode || !studentName) {
    return <Navigate to="/" replace />;
  }

  return children;
};

export default StudentPrivateRoute;