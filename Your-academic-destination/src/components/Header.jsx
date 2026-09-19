import React from "react";

const Header = ({ logos = [], tagline = "", date = "" }) => {
  return (
    <header className="card-header">
      <div className="logo-row">
        {logos.map((src, index) => (
          <img key={index} src={src} alt="شعار" className="header-logo" />
        ))}
      </div>
      <p className="header-tagline">{tagline}</p>
      <p className="header-date">{date}</p>
    </header>
  );
};

export default Header;