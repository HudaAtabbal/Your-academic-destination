import React from 'react';
import HeaderStep from '../../components/HeaderStep';
import BottomNav from '../../components/BottomNav';
import '../../style/AcademicGuide.css';

// ⚠️ هاد الدليل مبني بالكامل كملف HTML/CSS/JS مستقل (فيه نظام رسوم SVG متحركة،
// كروت تنقلب، نوافذ منبثقة...) — بدل ما "نترجمه" يدوياً لـ React (خطر كبير نكسر
// شي بالنقل)، بنستضيفه كما هو بالضبط جوا iframe. لازم تحطي ملف major-guide.html
// (يلي بعتّلك ياه لحاله) داخل مجلد public/ بمشروعك، بحيث يصير الرابط:
// public/major-guide.html
const AcademicGuide = () => {
  return (
    <div className="ag-card-wrapper">
      <div className="ag-card-container">

        <HeaderStep
          title="الدليل الأكاديمي"
          stepText="42 فرعاً على 6 مستويات صعوبة"
          onBack={() => window.history.back()}
        />

        <iframe
          src="/major-guide.html"
          title="الدليل الأكاديمي"
          className="ag-guide-iframe"
        />

        <BottomNav />

      </div>
    </div>
  );
};

export default AcademicGuide;