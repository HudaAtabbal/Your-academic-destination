import React from 'react';

const MajorCard = ({ title, cluster, difficulty, dotColor, onClick }) => {
  return (
    <div className="major-card" onClick={onClick}>
      <div className="major-arrow">&rarr;</div>
      <div className="major-info">
        <div className="major-title-row">
          <span className="color-dot" style={{ backgroundColor: dotColor }}></span>
          <h3 className="major-title">{title}</h3>
        </div>
        <p className="major-details">
          {cluster} • {difficulty}
        </p>
      </div>
    </div>
  );
};

export default MajorCard;