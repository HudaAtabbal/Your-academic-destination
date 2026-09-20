import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

/**
 * GuestOnlyRoute — لصفحات الترحيب/التسجيل.
 *  1. studentCode + studentName (موثّق) → /my-card
 *  2. pendingStudentCode فقط:
 *     - على صفحة الترحيب "/" → /otp مع autoResend (إرسال رمز جديد تلقائياً)
 *     - على صفحات register-step* → نسمح (عشان "تعديل رقم الهاتف" يشتغل)
 *     - غير هيك → /otp بدون إرسال
 */
const GuestOnlyRoute = ({ children }) => {
  const { pathname } = useLocation();
  const studentCode = localStorage.getItem('studentCode');
  const studentName = localStorage.getItem('studentName');
  const pendingStudentCode = localStorage.getItem('pendingStudentCode');

  if (studentCode && studentName) {
    return <Navigate to="/my-card" replace />;
  }

  if (pendingStudentCode) {
    if (pathname.startsWith('/register-step')) {
      return children;
    }
    if (pathname === '/') {
      return <Navigate to="/otp" replace state={{ autoResend: true }} />;
    }
    return <Navigate to="/otp" replace />;
  }

  return children;
};

export default GuestOnlyRoute;