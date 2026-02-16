import React, { useState } from 'react';

const LanguageScreen = ({ onNext, onPrev, onStartTranscription }) => {
  const [sourceLanguage, setSourceLanguage] = useState('Auto-detect');
  const [targetLanguage, setTargetLanguage] = useState('Same as Original (No Translation)');

  const screenStyle = {
    minHeight: '100vh',
    background: '#f8fafc',
    padding: '24px'
  };

  const containerStyle = {
    maxWidth: '600px',
    margin: '0 auto',
    padding: '80px 0'
  };

  const headerStyle = {
    textAlign: 'center',
    marginBottom: '48px'
  };

  const iconStyle = {
    width: '64px',
    height: '64px',
    background: '#3b82f6',
    borderRadius: '12px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 24px auto',
    color: 'white',
    fontSize: '24px'
  };

  const formGroupStyle = {
    marginBottom: '24px'
  };

  const labelStyle = {
    display: 'block',
    fontSize: '14px',
    fontWeight: '500',
    color: '#374151',
    marginBottom: '8px'
  };

  const selectStyle = {
    width: '100%',
    padding: '12px 16px',
    fontSize: '16px',
    border: '2px solid #e5e7eb',
    borderRadius: '8px',
    background: 'white',
    color: '#1f2937',
    appearance: 'none',
    backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
    backgroundPosition: 'right 12px center',
    backgroundRepeat: 'no-repeat',
    backgroundSize: '16px'
  };

  const buttonStyle = {
    width: '100%',
    padding: '16px',
    fontSize: '16px',
    fontWeight: '600',
    border: 'none',
    borderRadius: '8px',
    background: '#3b82f6',
    color: 'white',
    cursor: 'pointer',
    marginTop: '32px'
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
          <div style={iconStyle}>🌐</div>
          <h2 style={{ color: '#1e293b', fontSize: '32px', fontWeight: '700', marginBottom: '12px' }}>
            Choose Translation Language
          </h2>
          <p style={{ color: '#64748b', fontSize: '16px', lineHeight: '1.6', margin: '0' }}>
            Select the target language for translation (optional)
          </p>
        </div>

        <div style={formGroupStyle}>
          <label style={labelStyle}>
            Source Language
          </label>
          <select
            style={selectStyle}
            value={sourceLanguage}
            onChange={(e) => setSourceLanguage(e.target.value)}
          >
            <option value="Auto-detect">Auto-detect</option>
            <option value="English">English</option>
            <option value="Spanish">Spanish</option>
            <option value="French">French</option>
            <option value="German">German</option>
            <option value="Italian">Italian</option>
            <option value="Portuguese">Portuguese</option>
            <option value="Russian">Russian</option>
            <option value="Japanese">Japanese</option>
            <option value="Korean">Korean</option>
            <option value="Chinese">Chinese</option>
            <option value="Hindi">Hindi</option>
            <option value="Telugu">Telugu</option>
          </select>
        </div>

        <div style={formGroupStyle}>
          <label style={labelStyle}>
            Target Language
          </label>
          <select
            style={selectStyle}
            value={targetLanguage}
            onChange={(e) => setTargetLanguage(e.target.value)}
          >
            <option value="Same as Original (No Translation)">Same as Original (No Translation)</option>
            <option value="en">English</option>
            <option value="hi">Hindi</option>
            <option value="te">Telugu</option>
            <option value="ta">Tamil</option>
            <option value="kn">Kannada</option>
            <option value="ml">Malayalam</option>
            <option value="gu">Gujarati</option>
            <option value="mr">Marathi</option>
            <option value="bn">Bengali</option>
            <option value="or">Odia</option>
            <option value="pa">Punjabi</option>
            <option value="as">Assamese</option>
          </select>
        </div>

        <button
          style={buttonStyle}
          onClick={() => onStartTranscription(targetLanguage, sourceLanguage)}
          onMouseOver={(e) => e.target.style.background = '#2563eb'}
          onMouseOut={(e) => e.target.style.background = '#3b82f6'}
        >
          Continue
        </button>
      </div>
    </div>
  );
};

export default LanguageScreen;