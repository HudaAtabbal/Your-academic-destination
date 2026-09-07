import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../../style/SelectStationPage.css';

// أسماء الأدوار بالعربي — لبناء نص المستخدم (userInfo) من بيانات الحساب المخزّنة فعلياً
const ROLE_LABELS = {
  super_admin: 'المدير العام',
  students_admin: 'مدير بيانات الطلاب',
  gate_scanner: 'مسؤول المسح',
  college_staff: 'مسؤول الكلية',
};

// كل محطة بتودّي على شاشة حقيقية بالراوتر
const STATION_ROUTES = {
  guidance_corner: '/team-college', // ركن التوجيه
  faculty_gate: '/team-tour', // باب الكلية (جولة تعريفية)
  consultation_gate: '/team-consultation', // باب الاستشارة
};

const SelectStationPage = () => {
  const navigate = useNavigate();

  // بيانات الحساب المسجّل دخوله فعلياً (اتخزنت وقت تسجيل الدخول بـ TeamLoginPage)
  const username = localStorage.getItem('accountUsername') || '';
  const roleType = localStorage.getItem('accountRole') || '';
  const college = localStorage.getItem('accountCollege') || '';
  const roleLabel = ROLE_LABELS[roleType] || roleType;
  const userInfo = [username, roleLabel, college].filter(Boolean).join(' • ');

  const stations = [
    {
      id: 'guidance_corner',
      title: 'ركن التوجيه',
      description: 'جوّا مبنى كلية ثانية — يحدد وين رايح الطالب: جولة ولا استشارة',
    },
    {
      id: 'faculty_gate',
      title: 'باب الكلية',
      description: 'يأكد إنّه الطالب فعلاً زار هالكلية (جولة تعريفية)',
    },
    {
      id: 'consultation_gate',
      title: 'باب الاستشارة',
      description: 'يأكد إنّه الطالب فعلاً دخل الاستشارة الفردية',
    },
  ];

  const handleStationClick = (stationId) => {
    const route = STATION_ROUTES[stationId];
    if (route) {
      navigate(route);
    }
  };

  return (
    <div className="ssp-mobile-wrapper">
      <div className="ssp-mobile-card">
        
        {/* Header Section */}
        <header className="ssp-header">
          
          <div className="ssp-header-text">
            <h1 className="ssp-title">اختر محطتك</h1>
            <span className="ssp-user-info">{userInfo}</span>
          </div>
        </header>

        {/* Stations Selection Options */}
        <main className="ssp-content">
          <div className="ssp-options-list">
            {stations.map((station) => (
              <button
                key={station.id}
                type="button"
                className="ssp-option-card"
                onClick={() => handleStationClick(station.id)}
              >
                <div className="ssp-option-arrow">←</div>
                <div className="ssp-option-details">
                  <h2 className="ssp-option-title">{station.title}</h2>
                  <p className="ssp-option-desc">{station.description}</p>
                </div>
              </button>
            ))}
          </div>
        </main>

      </div>
    </div>
  );
};

export default SelectStationPage;