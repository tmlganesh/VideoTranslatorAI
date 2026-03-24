import React from 'react';

const UploadScreen = ({ 
  videoUrl, 
  setVideoUrl, 
  onNext, 
  onPrev 
}) => {
  const isValid = !!videoUrl;

  const screenStyle = {
    minHeight: '100vh',
    background: '#f8fafc',
    padding: '24px'
  };

  const containerStyle = {
    maxWidth: '600px',
    margin: '0 auto',
    padding: '48px 0'
  };

  const headerStyle = {
    textAlign: 'center',
    marginBottom: '48px'
  };

  const uploadOptionStyle = {
    background: '#ffffff',
    border: '2px solid #3b82f6',
    borderRadius: '12px',
    padding: '40px 32px',
    transition: 'all 0.2s ease',
    textAlign: 'center',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
  };

  return (
    <div style={screenStyle}>
      <div style={containerStyle}>
        <button 
          onClick={onPrev}
          style={{
            background: 'none',
            border: 'none',
            color: '#64748b',
            fontSize: '14px',
            cursor: 'pointer',
            padding: '8px 0',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}
        >
          ← Back
        </button>
        
        <div style={headerStyle}>
          <h2 style={{ color: '#1e293b', fontSize: '32px', fontWeight: '700', marginBottom: '12px' }}>
            Paste Video Link
          </h2>
          <p style={{ color: '#64748b', fontSize: '18px', lineHeight: '1.6', margin: '0' }}>
            Enter a URL from YouTube, Vimeo, or other platforms to start transcribing
          </p>
        </div>
        
        <div style={uploadOptionStyle}>
          <div style={{ fontSize: '48px', marginBottom: '24px', color: '#3b82f6' }}>🔗</div>
          <div style={{ marginBottom: '24px' }}>
            <input
              type="url"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              placeholder="https://youtube.com/watch?v=..."
              style={{
                width: '100%',
                padding: '16px',
                fontSize: '16px',
                border: '2px solid #e2e8f0',
                borderRadius: '8px',
                background: '#f8fafc',
                outline: 'none',
                color: '#1e293b',
                boxSizing: 'border-box',
                transition: 'border-color 0.2s ease'
              }}
              onFocus={(e) => e.target.style.borderColor = '#3b82f6'}
              onBlur={(e) => e.target.style.borderColor = '#e2e8f0'}
            />
          </div>
          <p style={{ color: '#9ca3af', fontSize: '14px', margin: '0' }}>
            Supports YouTube, Vimeo, Dailymotion and direct video URLs
          </p>
        </div>
        
        <div style={{ textAlign: 'center', marginTop: '48px' }}>
          <button 
            style={{
              padding: '16px 64px',
              fontSize: '18px',
              fontWeight: '600',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              background: isValid ? '#3b82f6' : '#d1d5db',
              color: 'white',
              transition: 'all 0.2s ease',
              boxShadow: isValid ? '0 10px 15px -3px rgba(59, 130, 246, 0.3)' : 'none'
            }}
            onClick={onNext}
            disabled={!isValid}
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  );
};

export default UploadScreen;