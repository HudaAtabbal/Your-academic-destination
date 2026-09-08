import React from 'react';
import { Navigate } from 'react-router-dom';

/**
 * GuestOnlyRoute — عكس StudentPrivateRoute تماماً.
 * لصفحات الترحيب/التسجيل (/, register-step1-3) — هاي المفروض يشوفها بس طالب
 * "جديد" لسا ما بلش تسجيل. عندنا حالتين لطالب مش "جديد":
 *
 *  1. عنده studentCode بس (سجّل فعلاً، بس لسا ما تحقق من OTP) → منرجّعه يكمّل
 *     التحقق بـ /otp، مش نخليه يسجّل من جديد (بيصير تعارض عند الباك لنفس الرقم).
 *  2. عنده studentCode و studentName سوا (خلّص تسجيل وتحقق كامل) → منرجّعه
 *     مباشرة لبطاقته الجاهزة.
 *
 * الاستخدام بـ App.jsx:
 *   <Route path="/" element={<GuestOnlyRoute><WelcomePage/></GuestOnlyRoute>} />
 */
const GuestOnlyRoute = ({ children }) => {
  const studentCode = localStorage.getItem('studentCode');
  const studentName = localStorage.getItem('studentName');

  if (studentCode && studentName) {
    return <Navigate to="/my-card" replace />;
  }

  if (studentCode && !studentName) {
    return <Navigate to="/otp" replace />;
  }

  return children;
};

export default GuestOnlyRoute;