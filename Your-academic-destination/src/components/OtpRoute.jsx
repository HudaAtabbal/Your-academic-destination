import React from 'react';
import { Navigate } from 'react-router-dom';

/**
 * OtpRoute — بوابة صفحة التحقق /otp.
 * ما لازم حدا يوصل لهون إلا إذا مرق بعملية التسجيل وعنده pendingStudentCode:
 *
 *  1. عنده studentCode و studentName (خلّص التحقق) → منرجّعه لبطاقته.
 *  2. عنده pendingStudentCode (سجّل ولسا بدو يتحقق) → منسمح له.
 *  3. ولا واحد من هدول (فتح الرابط مباشرة) → منرجّعه لبداية التسجيل.
 *
 * الاستخدام بـ App.jsx:
 *   <Route path="/otp" element={<OtpRoute><OTP/></OtpRoute>} />
 */
const OtpRoute = ({ children }) => {
  const studentCode = localStorage.getItem('studentCode');
  const studentName = localStorage.getItem('studentName');
  const pendingStudentCode = localStorage.getItem('pendingStudentCode');

  if (studentCode && studentName) {
    return <Navigate to="/my-card" replace />;
  }

  if (pendingStudentCode) {
    return children;
  }

  return <Navigate to="/register-step1" replace />;
};

export default OtpRoute;
