import React from 'react';
import '../style/StepProgress.css';

const StepProgress = ({ totalSteps = 3, currentStep = 1 }) => (
  <div className="progress-container">
    {Array.from({ length: totalSteps }).map((_, index) => (
      <div
        key={index}
        className={`progress-bar ${index < currentStep ? 'active' : ''}`}
      />
    ))}
  </div>
);

export default StepProgress;