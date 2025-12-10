import React from 'react';

const ProgressBar = ({ currentStep, totalSteps = 5 }) => {
  const progressPercentage = (currentStep / totalSteps) * 100;

  const progressBarStyle = {
    width: '100%',
    height: '6px',
    background: 'rgba(255, 255, 255, 0.3)',
    borderRadius: '3px',
    marginBottom: '20px',
    overflow: 'hidden'
  };

  const progressFillStyle = {
    height: '100%',
    background: '#4facfe',
    borderRadius: '3px',
    transition: 'width 0.3s ease',
    width: `${progressPercentage}%`
  };

  return (
    <div style={progressBarStyle}>
      <div style={progressFillStyle}></div>
    </div>
  );
};

export default ProgressBar;