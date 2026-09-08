import React from 'react';
import { Navigate } from 'react-router-dom';
import { getAuthToken } from '../api/api';

/**
 * TeamPrivateRoute — بوابة حماية لكل صفحات فريق العمل/الإدارة.
 * إذا ما في توكن مخزّن (يعني ما سجّل دخول أصلاً)، بترجّعه فوراً لصفحة تسجيل الدخول
 * بدل ما تخليه يشوف صفحة فاضية (البيانات محمية من الباك أصلاً، بس هون منمنع
 * حتى وصوله لهيكل الصفحة نفسه من غير تسجيل دخول).
 *
 * الاستخدام بـ App.jsx:
 *   <Route path="/dashboard" element={<TeamPrivateRoute><GeneralDirectorDashboard/></TeamPrivateRoute>} />
 *
 * لو بدك كمان تقيّدي الصفحة بدور معيّن بس (مش أي حساب فريق):
 *   <Route path="/dashboard" element={<TeamPrivateRoute allowedRoles={['super_admin']}><GeneralDirectorDashboard/></TeamPrivateRoute>} />
 */
const TeamPrivateRoute = ({ children, allowedRoles }) => {
  const token = getAuthToken();

  if (!token) {
    return <Navigate to="/team-log" replace />;
  }

  if (allowedRoles && allowedRoles.length > 0) {
    const currentRole = localStorage.getItem('accountRole');
    if (!allowedRoles.includes(currentRole)) {
      return <Navigate to="/team-log" replace />;
    }
  }

  return children;
};

export default TeamPrivateRoute;