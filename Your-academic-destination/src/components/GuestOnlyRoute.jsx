import React from 'react';
import { Navigate } from 'react-router-dom';

/**
 * GuestOnlyRoute — عكس StudentPrivateRoute تماماً.
 * لصفحات الترحيب/التسجيل (/, register-step1-3) — هاي المفروض يشوفها بس طالب
 * "جديد" لسا ما بلش تسجيل. عندنا حالتين لطالب مش "جديد":
 *
 *  1. عنده studentCode و studentName سوا (خلّص تسجيل وتحقق كامل) → منرجّعه
 *     مباشرة لبطاقته الجاهزة.
 *  2. عنده pendingStudentCode بس (سجّل بس لسا ما تحقق من OTP) → منرجّعه
 *     يكمّل التحقق بـ /otp، مش نخليه يسجّل من جديد.
 *
 * ملاحظة: pendingStudentCode منفصل عن studentCode قصداً — هيك لو الطالب
 * ضغط "تعديل الرقم" من صفحة OTP ورجع لـ register-step3، ما بيكون عنده
 * studentCode رسمي بعد (بينكتب بس بعد نجاح OTP فعلياً)، فبيقدر يدخل
 * صفحات التسجيل عادي ويعدّل بياناته.
 *
 * الاستخدام بـ App.jsx:
 *   <Route path="/" element={<GuestOnlyRoute><WelcomePage/></GuestOnlyRoute>} />
 */
const GuestOnlyRoute = ({ children }) => {
  const studentCode = localStorage.getItem('studentCode');
  const studentName = localStorage.getItem('studentName');
  const pendingStudentCode = localStorage.getItem('pendingStudentCode');

  if (studentCode && studentName) {
    return <Navigate to="/my-card" replace />;
  }

  if (pendingStudentCode) {
    return <Navigate to="/otp" replace />;
  }

  return children;
};

export default GuestOnlyRoute;