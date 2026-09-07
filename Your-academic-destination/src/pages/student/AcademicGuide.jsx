import React, { useState } from 'react';
import HeaderStep from '../../components/HeaderStep';
import MajorCard from '../../components/MajorCard';
import BottomNav from '../../components/BottomNav';
import '../../style/AcademicGuide.css';

const AcademicGuide = () => {
  const [searchTerm, setSearchTerm] = useState('');

  const majors = [
    { id: 1, title: 'الطب البشري', cluster: 'تجمّع الطب', difficulty: 'متوسطة', dotColor: '#E53935' },
    { id: 2, title: 'المعلوماتية', cluster: 'تجمّع العلوم', difficulty: 'سهلة', dotColor: '#00695C' },
    { id: 3, title: 'الهندسة المعمارية', cluster: 'تجمّع العمارة', difficulty: 'متقدمة', dotColor: '#FF6D00' },
    { id: 4, title: 'الحقوق', cluster: 'تجمّع الآداب', difficulty: 'سهلة', dotColor: '#00897B' },
    { id: 5, title: 'الصيدلة', cluster: 'تجمّع الطب', difficulty: 'متوسطة', dotColor: '#7B1FA2' },
    { id: 6, title: 'الهندسة الزراعية', cluster: 'تجمّع الزراعة', difficulty: 'متوسطة', dotColor: '#C0CA33' },
    { id: 7, title: 'الهندسة المدنية', cluster: 'تجمّع المدنية', difficulty: 'متقدمة', dotColor: '#558B2F' },
  ];

  const filteredMajors = majors.filter((major) => {
    const query = searchTerm.trim();
    if (!query) return true;
    return (
      major.title.includes(query) ||
      major.cluster.includes(query) ||
      major.difficulty.includes(query)
    );
  });

  return (
    <div className="ag-card-wrapper">
      <div className="ag-card-container">
        
        <HeaderStep 
          title="الدليل الأكاديمي" 
          stepText="42 فرعاً على 6 مستويات صعوبة" 
          onBack={() => window.history.back()} 
        />

        

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

export default AcademicGuide;