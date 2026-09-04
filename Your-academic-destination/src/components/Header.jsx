import React from 'react';

const Header = ({ logoSrc, subtitle }) => {
  return (
    <header className="card-header">
      <div className="logo-wrapper">
        <img 
          src={logoSrc} 
          alt="اتحاد طلبة سوريا - فرع محافظة حمص" 
          className="logo-img"
        />
      </div>
      <p className="subtitle">{subtitle}</p>
    </header>
  );
};

export default Header;