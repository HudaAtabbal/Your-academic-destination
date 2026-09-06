import React, { useState } from 'react';
import StaffScanHeader from '../../components/StaffScanHeader';
import ScanBox from '../../components/ScanBox';
import ScanResultCard from '../../components/ScanResultCard';
import ScannerFooter from '../../components/ScannerFooter';
import '../../style/StaffScan.css';

// موك بيانات — لاحقاً بيتبدل بطلب فعلي للـ backend وقت مسح الـ QR الحقيقي
const MOCK_STUDENTS = [
  { name: 'سارة يوسف', code: 'R-03871' },
  { name: 'ليان حاج علي', code: 'R-11907' },
  { name: 'محمد الخطيب', code: 'R-08321' },
];

const ConsultationPage = () => {
  const [result, setResult] = useState(null);
  const [scanCount, setScanCount] = useState(26);

  const handleScan = () => {
    // موك: بنختار طالب عشوائي ونفترض نجاح المسح (لسا ما في تكرار حقيقي بدون backend)
    const student = MOCK_STUDENTS[Math.floor(Math.random() * MOCK_STUDENTS.length)];
    setResult({
      status: 'success',
      title: 'تفصّل — أول استشارة إلك',
      studentName: student.name,
      studentCode: student.code,
    });
    setScanCount((prev) => prev + 1);
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">
        <StaffScanHeader
          title="استشارة فردية — الطب البشري"
          username="nour_staff"
          role="مسؤول الكلية"
          location="باب الاستشارة"
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
            يُسمح للطالب بحضور استشارة واحدة بس طول الفعالية كلها — بغض النظر عن الكلية.
          </p>
        </main>

        <ScannerFooter count={scanCount} countLabel="استشارة اليوم" />
      </div>
    </div>
  );
};

export default ConsultationPage;