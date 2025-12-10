import React from 'react';

const LandingScreen = ({ onNext }) => {
  const headerStyle = {
    background: 'white',
    padding: '16px 24px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottom: '1px solid #e2e8f0'
  };

  const logoStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '20px',
    fontWeight: '600',
    color: '#1e293b'
  };

  const logoIconStyle = {
    width: '32px',
    height: '32px',
    background: '#3b82f6',
    borderRadius: '6px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    fontSize: '16px'
  };

  const navStyle = {
    display: 'flex',
    gap: '24px',
    alignItems: 'center'
  };

  const mainStyle = {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '80px 24px',
    textAlign: 'center'
  };

  const videoIconStyle = {
    width: '80px',
    height: '80px',
    background: '#3b82f6',
    borderRadius: '16px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 32px auto',
    color: 'white',
    fontSize: '32px'
  };

  const titleStyle = {
    fontSize: '48px',
    fontWeight: '700',
    color: '#1e293b',
    lineHeight: '1.1',
    marginBottom: '16px',
    maxWidth: '800px',
    margin: '0 auto 16px auto'
  };

  const descriptionStyle = {
    fontSize: '20px',
    color: '#64748b',
    lineHeight: '1.6',
    marginBottom: '48px',
    maxWidth: '600px',
    margin: '0 auto 48px auto'
  };

  const buttonContainerStyle = {
    display: 'flex',
    gap: '16px',
    justifyContent: 'center',
    flexWrap: 'wrap'
  };

  const primaryButtonStyle = {
    background: '#3b82f6',
    color: 'white',
    border: 'none',
    padding: '16px 32px',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
  };

  const secondaryButtonStyle = {
    background: 'white',
    color: '#374151',
    border: '1px solid #d1d5db',
    padding: '16px 32px',
    borderRadius: '8px',
    fontSize: '16px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'all 0.2s ease'
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f8fafc' }}>
      {/* Header */}
      <header style={headerStyle}>
        <div style={logoStyle}>
          <div style={logoIconStyle}>📹</div>
          TranscribeAI
        </div>
        <nav style={navStyle}>
          <a href="#" style={{ color: '#64748b', textDecoration: 'none' }}>Help</a>
          <button style={{
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '6px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer'
          }}>
            Sign In
          </button>
        </nav>
      </header>

      {/* Main Content */}
      <main style={mainStyle}>
        <div style={videoIconStyle}>📹</div>
        
        <h1 style={titleStyle}>
          Transcribe and Translate Videos Easily
        </h1>
        
        <p style={descriptionStyle}>
          Upload your videos or paste a link to automatically extract audio, 
          transcribe speech to text, and translate to any language using 
          advanced AI technology.
        </p>
        
        <div style={buttonContainerStyle}>
          <button 
            style={primaryButtonStyle}
            onClick={onNext}
            onMouseOver={(e) => e.target.style.background = '#2563eb'}
            onMouseOut={(e) => e.target.style.background = '#3b82f6'}
          >
            Get Started
          </button>
          <button style={secondaryButtonStyle}>
            Watch Demo
          </button>
        </div>
      </main>
    </div>
  );
};

export default LandingScreen;