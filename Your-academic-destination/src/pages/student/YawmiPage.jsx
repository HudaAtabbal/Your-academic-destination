import React from 'react';
import HeaderStep from '../../components/HeaderStep';
import BottomNav from '../../components/BottomNav';
import '../../style/AcademicGuide.css';

// ⚠️ هاد الملف (يومي) مبني كملف HTML/CSS/JS مستقل فيه برنامج الملتقى على شكل
// تابات الأيام الثلاثة — بدل ما "نترجمه" يدوياً لـ React، بنستضيفه كما هو
// بالضبط جوا iframe. الملف مستضاف على السيرفر ضمن مسار /yawmi/
const YawmiPage = () => {
  return (
    <div className="ag-card-wrapper">
      <div className="ag-card-container">

        <HeaderStep
          title="البرنامج اليومي"
          stepText="برنامج الملتقى على مدى الأيام الثلاثة"
        />

        <iframe
          src="/yawmi/"
          title="البرنامج اليومي"
          className="ag-guide-iframe"
        />

        <BottomNav />

      </div>
    </div>
  );
};

export default YawmiPage;