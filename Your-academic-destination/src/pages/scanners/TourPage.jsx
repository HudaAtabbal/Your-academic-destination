import React, { useState } from 'react';
import StaffScanHeader from '../../components/StaffScanHeader';
import ScanBox from '../../components/ScanBox';
import ScanResultCard from '../../components/ScanResultCard';
import ScannerFooter from '../../components/ScannerFooter';
import '../../style/StaffScan.css';

const MOCK_STUDENTS = [
  { name: 'ليان حاج علي', code: 'R-1190' },
  { name: 'سارة يوسف', code: 'R-0387' },
  { name: 'عمر أحمد العسورة', code: 'R-0248' },
];

const TourPage = () => {
  const [result, setResult] = useState(null);
  const [scanCount, setScanCount] = useState(42);

  const handleScan = () => {
    const student = MOCK_STUDENTS[Math.floor(Math.random() * MOCK_STUDENTS.length)];
    setResult({
      status: 'success',
      title: 'جولة — جولة الطب البشري',
      studentName: student.name,
      studentCode: student.code,
    });
    setScanCount((prev) => prev + 1);
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">
        <StaffScanHeader
          title="جولة تعريفية — الطب البشري"
          username="yousef_tour"
          role="مسؤول الجولة"
          location="باب الكلية"
        />

        <main className="card-body">
          <ScanBox onScan={handleScan} />

          <ScanResultCard
            status={result?.status}
            title={result?.title}
            studentName={result?.studentName}
            studentCode={result?.studentCode}
          />

          <p className="scan-rule-text">
            يمكن للطالب زيارة عدة كليات مختلفة، لكن لا يمكنه تسجيل حضور جولة نفس الكلية مرتين.
          </p>
        </main>

        <ScannerFooter count={scanCount} countLabel="مسحة مرفوعة" />
      </div>
    </div>
  );
};

export default TourPage;