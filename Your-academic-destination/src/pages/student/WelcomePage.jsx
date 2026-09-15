import React from "react";
import Header from "../../components/Header";
import InfoCard from "../../components/InfoCard";
import "../../style/WelcomePage.css";
import logo from "../../assets/English logo white-01.png";
import { useNavigate } from "react-router-dom";

const WelcomePage = () => {
  const navigate = useNavigate();
  return (
    <div className="wp-card-wrapper">
      <div className="wp-card-container">
        <Header logoSrc={logo} subtitle="جامعة حمص • 15–17 أيلول" />

        <main className="wp-card-body">
          <h1 className="wp-main-title">وجهتك الأكاديمية</h1>
          <span className="wp-badge">النسخة الثانية</span>

          <p className="wp-description">
            ثلاثة أيام تتعرّف فيها على كل كلية في الجامعة، وتسأل من دَرسها قَبلك.
          </p>

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