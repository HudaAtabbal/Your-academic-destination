import React, { useState } from 'react';
import StaffScanHeader from '../../components/StaffScanHeader';
import ScanBox from '../../components/ScanBox';
import ScanResultCard from '../../components/ScanResultCard';
import ScannerFooter from '../../components/ScannerFooter';
import '../../style/StaffScan.css';

const LECTURES = [
  { id: 'jobs-market', name: 'سوق العمل والمهن الصاعدة', hall: 'مدرج رئيسي' },
  { id: 'study-abroad', name: 'الدراسة بالخارج', hall: 'مدرج ب' },
  { id: 'majors-101', name: 'مقدمة عن التخصصات الجامعية', hall: 'مدرج رئيسي' },
];

// موك: طلاب سبق ومسحوا لنفس المحاضرة، لمحاكاة كشف التكرار
const ALREADY_SCANNED = ['R-0832'];

const MOCK_STUDENTS = [
  { name: 'محمد الخطيب', code: 'R-0832' }, // هاد مكرر (موجود فوق) — رح يطلع تحذير
  { name: 'ليان حاج علي', code: 'R-1190' },
  { name: 'سارة يوسف', code: 'R-0387' },
];

const StadiumPage = () => {
  const [selectedLectureId, setSelectedLectureId] = useState(LECTURES[0].id);
  const [result, setResult] = useState(null);
  const [scanCount, setScanCount] = useState(118);

  const selectedLecture = LECTURES.find((l) => l.id === selectedLectureId);

  const handleScan = () => {
    const student = MOCK_STUDENTS[Math.floor(Math.random() * MOCK_STUDENTS.length)];
    const isDuplicate = ALREADY_SCANNED.includes(student.code);

    if (isDuplicate) {
      setResult({
        status: 'error',
        title: 'مسحت من قبل لنفس المحاضرة',
        studentName: student.name,
        studentCode: student.code,
      });
    } else {
      setResult({
        status: 'success',
        title: `حضور — ${selectedLecture.name}`,
        studentName: student.name,
        studentCode: student.code,
      });
      setScanCount((prev) => prev + 1);
    }
  };

  const handleQuickRegister = () => {
    // موك: تسجيل الخط السريع لطالب بدون بطاقة/QR معه
    console.log('فتح تسجيل سريع بدون بطاقة للمحاضرة:', selectedLecture.name);
  };

  return (
    <div className="card-wrapper">
      <div className="card-container">
        <StaffScanHeader
          title="مسح عند المدرج"
          username="hadi_gate"
          role="مسؤول المسح"
          location={selectedLecture.hall}
        />

        <main className="card-body">
          <div>
            <p className="input-label" style={{ marginBottom: 8, color: '#71122B', fontWeight: 700 }}>
              المحاضرة الجارية الآن
            </p>
            <div className="lecture-select-wrapper">
              <select
                className="lecture-select"
                value={selectedLectureId}
                onChange={(e) => {
                  setSelectedLectureId(e.target.value);
                  setResult(null);
                }}
              >
                {LECTURES.map((lecture) => (
                  <option key={lecture.id} value={lecture.id}>
                    {lecture.name} · {lecture.hall}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <ScanBox onScan={handleScan} />

          <ScanResultCard
            status={result?.status}
            title={result?.title}
            studentName={result?.studentName}
            studentCode={result?.studentCode}
          />

          <button type="button" className="quick-register-btn" onClick={handleQuickRegister}>
            تسجيل الخط السريع (بدون بطاقة)
          </button>
        </main>

        <ScannerFooter count={scanCount} countLabel="مسحة مرفوعة" />
      </div>
    </div>
  );
};

export default StadiumPage;