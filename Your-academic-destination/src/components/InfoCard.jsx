import React from 'react';

const InfoCard = ({ title, text }) => {
  return (
    <div className="info-box">
      <h3 className="info-title">{title}</h3>
      <p className="info-text">{text}</p>
    </div>
  );
};

export default InfoCard;