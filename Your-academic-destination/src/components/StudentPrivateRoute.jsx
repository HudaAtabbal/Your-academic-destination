import React from 'react';
import { Navigate } from 'react-router-dom';

/**
 * StudentPrivateRoute — بوابة حماية لصفحات الطالب الشخصية (البطاقة، الاستبيان، النقاط)
 * يلي بدها studentCode موجود بـ localStorage (يعني الطالب خلّص تسجيل + تحقق OTP فعلاً،
 * أو استرجع بطاقته من FindCardPage). لو حاول حدا يفتح هالصفحات مباشرة بدون هيك،
 * بترجّعه لصفحة البداية بدل ما يشوف صفحة فاضية أو بيانات ناقصة.
 *
 * الاستخدام بـ App.jsx:
 *   <Route path="/my-card" element={<StudentPrivateRoute><MyCard/></StudentPrivateRoute>} />
 */
const StudentPrivateRoute = ({ children }) => {
  const studentCode = localStorage.getItem('studentCode');

  if (!studentCode) {
    return <Navigate to="/" replace />;
  }

  return children;
};

export default StudentPrivateRoute;