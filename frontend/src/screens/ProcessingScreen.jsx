import React, { useState, useEffect } from 'react';

const ProcessingScreen = ({ error, onRetry }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(120); // 2 minutes

  const steps = [
    { 
      id: 'extracting', 
      label: 'Extracting Audio', 
      icon: '✅', 
      status: 'complete',
      color: '#10b981'
    },
    { 
      id: 'transcribing', 
      label: 'Transcribing Speech', 
      icon: '⚙️', 
      status: 'in-progress',
      color: '#3b82f6'
    },
    { 
      id: 'translating', 
      label: 'Translating Text', 
      icon: '📄', 
      status: 'waiting',
      color: '#6b7280'
    }
  ];

  // Simulate progress animation
  useEffect(() => {
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 75) return prev;
        return prev + Math.random() * 3;
      });
    }, 200);

    const timeInterval = setInterval(() => {
      setTimeRemaining(prev => Math.max(0, prev - 1));
    }, 1000);

    return () => {
      clearInterval(progressInterval);
      clearInterval(timeInterval);
    };
  }, []);

  const screenStyle = {
    minHeight: '100vh',
    background: '#f8fafc',
    padding: '24px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  };

  const containerStyle = {
    maxWidth: '600px',
    width: '100%',
    textAlign: 'center'
  };

  const iconContainerStyle = {
    width: '80px',
    height: '80px',
    background: 'linear-gradient(135deg, #60a5fa, #3b82f6)',
    borderRadius: '20px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 32px auto',
    animation: 'spin 2s linear infinite'
  };

  const titleStyle = {
    color: '#1e293b',
    fontSize: '32px',
    fontWeight: '700',
    marginBottom: '12px'
  };

  const subtitleStyle = {
    color: '#64748b',
    fontSize: '16px',
    lineHeight: '1.6',
    marginBottom: '48px'
  };

  const stepsContainerStyle = {
    marginBottom: '32px'
  };

  const stepStyle = {
    display: 'flex',
    alignItems: 'center',
    padding: '16px 0',
    borderBottom: '1px solid #f1f5f9'
  };

  const stepIconStyle = (step) => ({
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: '16px',
    fontSize: '14px',
    background: step.status === 'complete' ? '#10b981' : 
                step.status === 'in-progress' ? '#3b82f6' : '#e5e7eb',
    color: step.status === 'waiting' ? '#6b7280' : 'white'
  });

  const stepLabelStyle = {
    flex: 1,
    textAlign: 'left',
    fontSize: '16px',
    fontWeight: '500',
    color: '#1e293b'
  };

  const stepStatusStyle = (step) => ({
    fontSize: '14px',
    fontWeight: '500',
    color: step.status === 'complete' ? '#10b981' : 
           step.status === 'in-progress' ? '#3b82f6' : '#9ca3af'
  });

  const progressBarContainerStyle = {
    width: '100%',
    height: '8px',
    background: '#e5e7eb',
    borderRadius: '4px',
    marginBottom: '24px',
    overflow: 'hidden'
  };

  const progressBarStyle = {
    height: '100%',
    background: 'linear-gradient(90deg, #3b82f6, #60a5fa)',
    borderRadius: '4px',
    width: `${progress}%`,
    transition: 'width 0.3s ease'
  };

  const timeStyle = {
    color: '#64748b',
    fontSize: '14px',
    marginBottom: '24px'
  };

  const cancelButtonStyle = {
    background: 'white',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    padding: '12px 24px',
    fontSize: '14px',
    color: '#374151',
    cursor: 'pointer'
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div style={screenStyle}>
      <div style={containerStyle}>
        <div style={iconContainerStyle}>
          <span style={{ fontSize: '32px', color: 'white' }}>⚙️</span>
        </div>
        
        <h2 style={titleStyle}>
          Processing Your Video
        </h2>
        
        <p style={subtitleStyle}>
          Please wait while we extract and transcribe your content
        </p>
        
        <div style={stepsContainerStyle}>
          {steps.map((step, index) => (
            <div key={step.id} style={stepStyle}>
              <div style={stepIconStyle(step)}>
                {step.icon}
              </div>
              <div style={stepLabelStyle}>
                {step.label}
              </div>
              <div style={stepStatusStyle(step)}>
                {step.status === 'complete' ? '✓ Complete' :
                 step.status === 'in-progress' ? 'In Progress...' : 'Waiting...'}
              </div>
            </div>
          ))}
        </div>
        
        <div style={progressBarContainerStyle}>
          <div style={progressBarStyle}></div>
        </div>
        
        <p style={timeStyle}>
          Estimated time remaining: {Math.floor(timeRemaining / 60)} minutes
        </p>
        
        <button style={cancelButtonStyle}>
          Cancel Process
        </button>
        
        {error && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid #fca5a5',
            borderRadius: '8px',
            padding: '16px',
            marginTop: '24px',
            color: '#dc2626'
          }}>
            ⚠️ {error}
            <button 
              onClick={onRetry}
              style={{
                background: '#dc2626',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                padding: '8px 16px',
                marginLeft: '12px',
                cursor: 'pointer'
              }}
            >
              🔄 Try Again
            </button>
          </div>
        )}
      </div>
      
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default ProcessingScreen;