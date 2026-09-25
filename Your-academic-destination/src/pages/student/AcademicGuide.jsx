import React from 'react';
import HeaderStep from '../../components/HeaderStep';
import BottomNav from '../../components/BottomNav';
import usePageVisit from '../../hooks/usePageVisit';
import '../../style/AcademicGuide.css';

// ⚠️ هاد الدليل مبني بالكامل كملف HTML/CSS/JS مستقل (فيه نظام رسوم SVG متحركة,
// كروت تنقلب، نوافذ منبثقة...) — بدل ما "نترجمه" يدوياً لـ React (خطر كبير نكسر
// شي بالنقل)، بنستضيفه كما هو بالضبط جوا iframe. الملف مستضاف مع التطبيق على
// /app/major-guide.html
//
// `active` بيوصلنا من StudentTabsLayout — التبويب الظاهر حالياً. التتبّع بينبلّش
// بس وهو هالتبويب مفتوح، وبيقفّ لما الطالب ينقّل لتبويب تاني.
const AcademicGuide = ({ active }) => {
  usePageVisit(Boolean(active), 'academic-guide');

  return (
    <div className="ag-card-wrapper">
      <div className="ag-card-container">

        <HeaderStep
          title="الدليل الأكاديمي"
          stepText="كل ما تحتاج معرفته عن الكليات"
        />

        <iframe
          src="/app/major-guide.html"
          title="الدليل الأكاديمي"
          className="ag-guide-iframe"
        />

        <BottomNav />

      </div>
    </div>
  );
};

export default AcademicGuide;