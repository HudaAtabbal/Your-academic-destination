import React, { useState } from 'react';
import HeaderStep from '../../components/HeaderStep';
import MajorCard from '../../components/MajorCard';
import BottomNav from '../../components/BottomNav';
import '../../style/AcademicGuide.css';

const MapPage = () => {
  const [searchTerm, setSearchTerm] = useState('');

  return (
    <div className="ag-card-wrapper">
      <div className="ag-card-container">
        
        <HeaderStep 
          title="خريطة الجامعة" 
          stepText="طريقك الى الكلية" 
          onBack={() => window.history.back()} 
        />

        <main className="ag-scrollable-content">
          <div className="ag-coming-soon">
            <svg
              className="ag-coming-soon-icon"
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#134F47"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M6 2h12" />
              <path d="M6 22h12" />
              <path d="M6 2c0 5 4 6 6 8-2 2-6 3-6 8" />
              <path d="M18 2c0 5-4 6-6 8 2 2 6 3 6 8" />
            </svg>
            <h2 className="ag-coming-soon-title">قريباً</h2>
            <p className="ag-coming-soon-text">
             خريطة الجامعة قيد التجهيز ...
            </p>
          </div>
        </main>

        {/* Search Bar
        <div className="ag-search-wrapper">
          <svg
            className="ag-search-icon"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="7" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            placeholder="دوّري عن تخصص، تجمّع، أو مستوى صعوبة..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="ag-search-input"
          />
        </div>

        <main className="ag-scrollable-content">
          <div className="ag-majors-list">
            {filteredMajors.length > 0 ? (
              filteredMajors.map((major) => (
                <MajorCard 
                  key={major.id}
                  title={major.title}
                  cluster={major.cluster}
                  difficulty={major.difficulty}
                  dotColor={major.dotColor}
                  onClick={() => console.log('Selected:', major.title)}
                />
              ))
            ) : (
              <p className="ag-no-results">ما لقينا نتائج مطابقة</p>
            )}
          </div>

          {!searchTerm && (
            <p className="ag-scroll-hint">و 35 فرعاً إضافياً... اسحب للأسفل</p>
          )}
        </main> */}

        <BottomNav />

      </div>
    </div>
  );
};

export default MapPage;