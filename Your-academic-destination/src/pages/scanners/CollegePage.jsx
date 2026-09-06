import React, { useState } from 'react';
import StaffScanHeader from '../../components/StaffScanHeader';
import ScanBox from '../../components/ScanBox';
import ScannerFooter from '../../components/ScannerFooter';
import '../../style/StaffScan.css';

const CollegePage = () => {
  const [scannedStudent, setScannedStudent] = useState(null);
  const [choice, setChoice] = useState(null);
  const [scanCount, setScanCount] = useState(87);

  const handleScan = () => {
    // موك: طالب واحد ثابت للتجربة (لاحقاً بيجي من الـ backend الفعلي)
    setScannedStudent({ name: 'ليان حاج علي', code: 'R-11907' });
    setChoice(null);
  };

  const handleChoice = (option) => {
    setChoice(option);
    // هون منسجل "توجيه" بس، مش حضور فعلي — الحضور الحقيقي عند باب الكلية/الاستشارة
    setScanCount((prev) => prev + 1);
  };

  return (
    <div className="ss-card-wrapper">
      <div className="ss-card-container">
        <StaffScanHeader
          title="ركن التوجيه — الطب البشري"
          username="rima_staff"
          role="مسؤول الكلية"
          location="داخل مبنى كلية الهندسة"
        />

        <main className="ss-body">
          <ScanBox caption="امسح رمز الطالب لتوجيهه" onScan={handleScan} />

          {scannedStudent && (
            <div className="ss-orientation-prompt">
              <h3 className="ss-orientation-question">
                وين رايح {scannedStudent.name}؟ ({scannedStudent.code})
              </h3>
              <div className="ss-orientation-options">
                <button
                  type="button"
                  className={`ss-orientation-btn ${choice === 'consultation' ? 'selected' : ''}`}
                  onClick={() => handleChoice('consultation')}
                >
                  استشارة فردية
                </button>
                <button
                  type="button"
                  className={`ss-orientation-btn ${choice === 'tour' ? 'selected' : ''}`}
                  onClick={() => handleChoice('tour')}
                >
                  جولة الكلية
                </button>
              </div>
            </div>
          )}

          <p className="ss-rule-text">
            هاد بس توجيه — الحضور الفعلي بينسجّل عند باب الكلية أو باب الاستشارة تحديداً.
          </p>
        </main>

        <ScannerFooter count={scanCount} countLabel="توجيه اليوم" />
      </div>
    </div>
  );
};

export default CollegePage;