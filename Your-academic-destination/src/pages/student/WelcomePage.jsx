import React from "react";
import Header from "../../components/Header";
import InfoCard from "../../components/InfoCard";
import "../../style/WelcomePage.css";
import unionLogo from "../../assets/whited-logo-1.png";
import asset2 from "../../assets/asset-2.png";
import homsWhite from "../../assets/homs-university-white.png";
import faceitLogo from "../../assets/destination-white-01.png";
import { useNavigate } from "react-router-dom";

const WelcomePage = () => {
  const navigate = useNavigate();
  return (
    <div className="wp-card-wrapper">
      <div className="wp-card-container">
        <Header
          logos={[unionLogo, homsWhite, asset2, faceitLogo]}
          tagline="ثلاثة أيام تتعرّف فيها على كل كلية في الجامعة، وتسأل من دَرسها قَبلك."
          date="التواريخ: ٢٣ ، ٢٤ و ٢٦ أيلول"
        />

        <main className="wp-card-body">
          <h1 className="wp-main-title">وجهتك الأكاديمية</h1>
          <span className="wp-badge">النسخة الثانية</span>

          <InfoCard
            title="سجّل من البيت، وادخل من الخط السريع"
            text="التسجيل شرط الدخول. تحصل على  بطاقة برمز QR خاص بك تربطك بكل نشاط تحضره."
          />

          <div className="wp-actions">
            <button
              className="wp-btn wp-btn-primary"
              onClick={() => navigate("/register-step1")}
            >
              سجّل الآن • دقيقتين &larr;
            </button>
            <button
              className="wp-btn wp-btn-secondary"
              onClick={() => navigate("/find-card")}
            >
             لديَّ بطاقة 
            </button>
          </div>
        </main>
      </div>
    </div>
  );
};

export default WelcomePage;