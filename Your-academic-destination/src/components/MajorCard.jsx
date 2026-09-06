import React from 'react';

const MajorCard = ({ title, cluster, difficulty, dotColor, onClick }) => {
  return (
    <div className="ag-major-card" onClick={onClick}>
      <div className="ag-major-arrow">&rarr;</div>
      <div className="ag-major-info">
        <div className="ag-major-title-row">
          <span className="ag-color-dot" style={{ backgroundColor: dotColor }}></span>
          <h3 className="ag-major-title">{title}</h3>
        </div>
        <p className="ag-major-details">
          {cluster} • {difficulty}
        </p>
      </div>
    </div>
  );
};

export default MajorCard;