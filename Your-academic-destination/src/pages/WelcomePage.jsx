import React from "react";
import Header from "../components/Header";
import InfoCard from "../components/InfoCard";
import "../style/WelcomePage.css";
import logo from "../assets/English logo white-01.png";
import { useNavigate } from "react-router-dom";

const WelcomePage = () => {
  const navigate = useNavigate();
  return (
    <div className="card-wrapper">
      <div className="card-container">
        <Header logoSrc={logo} subtitle="جامعة حمص • 15–17 أيلول" />

        <main className="card-body">
          <h1 className="main-title">وجهتك الأكاديمية</h1>
          <span className="badge">النسخة الثانية</span>

          <p className="description">
            ثلاثة أيام تتعرّف فيها على كل كلية في الجامعة، وتسأل من درسها قبلك.
          </p>

          <InfoCard
            title="سجّل من البيت، واخل من الخط السريع"
            text="التسجيل شرط الدخول. بتاخد بطاقة برمز QR خاص فيك، وبتربطك بكل نشاط تحضره."
          />

          <div className="actions">
            <button
              className="btn btn-primary"
              onClick={() => navigate("/register-step1")}
            >
              سجّل الآن • دقيقتين &larr;
            </button>
            <button className="btn btn-secondary">عندي بطاقة من قبل</button>
          </div>
        </main>
      </div>
    </div>
  );
};

export default WelcomePage;
