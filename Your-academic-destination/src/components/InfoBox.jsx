import React from 'react';

const InfoBox = ({ text }) => {
  return (
    <div className="note-box">
      <p className="note-text">{text}</p>
    </div>
  );
};

export default InfoBox;