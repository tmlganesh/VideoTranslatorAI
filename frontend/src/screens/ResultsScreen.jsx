import React from 'react';

const ResultsScreen = ({ transcriptionResult, translationResult, targetLanguage, detectedLanguage, onNewTranscription }) => {
  // Use actual transcription data or fallback
  const actualTranscription = transcriptionResult || `There was an idea stark knows this called the Avengers Initiative. The idea was to bring together a group of remarkable people, see if they could become something more.

See if they could work together when we needed them to, to fight the battles that we never could. Phil Coulson died still believing in that idea, in heroes.

Well, it's an old fashioned notion. But I think it's time we give it a try. We need a response team. These people are dangerous.`;
  
  // Use real translation from Sarvam AI or show message if no translation
  const actualTranslation = translationResult && translationResult.trim() !== "" ? translationResult : null;
  
  // Language name mapping for display
  const getLanguageName = (langCode) => {
    const langMap = {
      'en': 'English',
      'hi': 'Hindi', 
      'te': 'Telugu',
      'ta': 'Tamil',
      'kn': 'Kannada',
      'ml': 'Malayalam',
      'gu': 'Gujarati',
      'mr': 'Marathi',
      'bn': 'Bengali',
      'or': 'Odia',
      'pa': 'Punjabi',
      'as': 'Assamese'
    };
    return langMap[langCode] || langCode;
  };

  // Helper function to format transcription with timestamps
  const formatTranscriptionWithTimestamps = (text) => {
    if (!text) return [];
    
    // Split transcription into sentences and add timestamps
    const sentences = text.split(/[.!?]+/).filter(s => s.trim());
    const formattedLines = [];
    
    sentences.forEach((sentence, index) => {
      if (sentence.trim()) {
        const minutes = Math.floor(index * 15 / 60);
        const seconds = (index * 15) % 60;
        const timestamp = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}:00`;
        formattedLines.push({
          timestamp,
          text: sentence.trim() + '.'
        });
      }
    });
    
    return formattedLines;
  };

  const transcriptionLines = formatTranscriptionWithTimestamps(actualTranscription);

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
  };

  const handleDownload = (text, filename) => {
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const screenStyle = {
    minHeight: '100vh',
    background: '#f8fafc',
    padding: '24px'
  };

  const containerStyle = {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '48px 0'
  };

  const headerStyle = {
    textAlign: 'center',
    marginBottom: '48px'
  };

  const successIconStyle = {
    width: '64px',
    height: '64px',
    background: '#10b981',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '0 auto 24px auto',
    color: 'white',
    fontSize: '24px'
  };

  const columnsStyle = {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '24px',
    marginBottom: '48px'
  };

  const columnStyle = {
    background: 'white',
    borderRadius: '12px',
    padding: '24px',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
  };

  const columnHeaderStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '16px',
    paddingBottom: '12px',
    borderBottom: '1px solid #f1f5f9'
  };

  const columnTitleStyle = {
    fontSize: '18px',
    fontWeight: '600',
    color: '#1e293b'
  };

  const metaStyle = {
    fontSize: '12px',
    color: '#64748b',
    marginBottom: '16px'
  };

  const textContentStyle = {
    fontSize: '14px',
    lineHeight: '1.6',
    color: '#374151',
    whiteSpace: 'pre-wrap',
    maxHeight: '300px',
    overflowY: 'auto'
  };

  const timestampStyle = {
    color: '#9ca3af',
    fontSize: '12px',
    fontFamily: 'monospace',
    marginRight: '12px',
    minWidth: '60px'
  };

  const textLineStyle = {
    display: 'flex',
    alignItems: 'flex-start',
    marginBottom: '12px'
  };

  const iconButtonStyle = {
    background: 'none',
    border: 'none',
    color: '#6b7280',
    cursor: 'pointer',
    padding: '4px',
    fontSize: '16px'
  };

  const actionsStyle = {
    display: 'flex',
    gap: '12px',
    justifyContent: 'center',
    flexWrap: 'wrap',
    marginBottom: '48px'
  };

  const buttonStyle = {
    padding: '12px 24px',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    border: 'none',
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  };

  const primaryButtonStyle = {
    ...buttonStyle,
    background: '#3b82f6',
    color: 'white'
  };

  const secondaryButtonStyle = {
    ...buttonStyle,
    background: '#10b981',
    color: 'white'
  };

  const tertiaryButtonStyle = {
    ...buttonStyle,
    background: '#8b5cf6',
    color: 'white'
  };

  const shareButtonStyle = {
    ...buttonStyle,
    background: 'white',
    color: '#374151',
    border: '1px solid #d1d5db'
  };

  const startNewButtonStyle = {
    ...buttonStyle,
    background: 'white',
    color: '#374151',
    border: '1px solid #d1d5db'
  };

  const footerStyle = {
    textAlign: 'center',
    paddingTop: '48px',
    borderTop: '1px solid #e2e8f0'
  };

  const logoStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    marginBottom: '12px'
  };

  const logoIconStyle = {
    width: '24px',
    height: '24px',
    background: '#3b82f6',
    borderRadius: '4px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    fontSize: '12px'
  };

  return (
    <div style={screenStyle}>
      <div style={containerStyle}>
        <div style={headerStyle}>
          <div style={successIconStyle}>✓</div>
          <h2 style={{ color: '#1e293b', fontSize: '32px', fontWeight: '700', marginBottom: '12px' }}>
            Transcription Complete!
          </h2>
          <p style={{ color: '#64748b', fontSize: '16px', margin: '0' }}>
            Your video has been successfully processed
          </p>
        </div>

        <div style={columnsStyle}>
          {/* Original Transcription */}
          <div style={columnStyle}>
            <div style={columnHeaderStyle}>
              <h3 style={columnTitleStyle}>Original Transcription</h3>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button 
                  style={iconButtonStyle}
                  onClick={() => handleCopy(actualTranscription)}
                  title="Copy transcription"
                >
                  📋
                </button>
                <button 
                  style={iconButtonStyle}
                  title="Edit transcription"
                >
                  ✏️
                </button>
              </div>
            </div>
            <div style={metaStyle}>
              {detectedLanguage?.name || 'Detected Language'} • {actualTranscription.split(' ').length} words • Auto-generated
            </div>
            <div style={textContentStyle}>
              {transcriptionLines.map((line, index) => (
                <div key={index} style={textLineStyle}>
                  <span style={timestampStyle}>{line.timestamp}</span>
                  <span>{line.text}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Translation */}
          <div style={columnStyle}>
            <div style={columnHeaderStyle}>
              <h3 style={columnTitleStyle}>Translation</h3>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button 
                  style={iconButtonStyle}
                  onClick={() => handleCopy(actualTranslation)}
                  title="Copy translation"
                  disabled={!actualTranslation}
                >
                  📋
                </button>
                <button 
                  style={iconButtonStyle}
                  title="Edit translation"
                >
                  ✏️
                </button>
              </div>
            </div>
            <div style={metaStyle}>
              {actualTranslation ? `${getLanguageName(targetLanguage)} • Translated from ${detectedLanguage?.name || 'Auto-detected'}` : 'No translation requested'}
            </div>
            <div style={textContentStyle}>
              {actualTranslation ? (
                <div style={textLineStyle}>
                  <span style={timestampStyle}>00:00:00</span>
                  <span>{actualTranslation}</span>
                </div>
              ) : (
                <div style={textLineStyle}>
                  <span style={{ ...timestampStyle, color: '#9ca3af' }}>--:--:--</span>
                  <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>No translation was requested for this transcription.</span>
                </div>
              )}
            </div>
          </div>
        </div>

        <div style={actionsStyle}>
          <button 
            style={primaryButtonStyle}
            onClick={() => handleDownload(sampleTranscription, 'transcription.txt')}
          >
            📥 Download TXT
          </button>
          <button 
            style={secondaryButtonStyle}
            onClick={() => handleDownload(sampleTranscription, 'transcription.docx')}
          >
            📄 Download DOCX
          </button>
          <button 
            style={tertiaryButtonStyle}
            onClick={() => handleDownload(sampleTranscription, 'transcription.srt')}
          >
            � Download SRT
          </button>
          <button style={shareButtonStyle}>
            🔗 Share Results
          </button>
          <button 
            style={startNewButtonStyle}
            onClick={onNewTranscription}
          >
            ➕ Start New
          </button>
        </div>

        <div style={footerStyle}>
          <div style={logoStyle}>
            <div style={logoIconStyle}>📹</div>
            <span style={{ fontWeight: '600', color: '#1e293b' }}>TranscribeAI</span>
          </div>
          <p style={{ color: '#64748b', fontSize: '14px', margin: '0 0 12px 0' }}>
            Powered by advanced AI technology for accurate transcription and translation
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '24px', fontSize: '12px', color: '#9ca3af' }}>
            <a href="#" style={{ color: 'inherit', textDecoration: 'none' }}>Privacy Policy</a>
            <a href="#" style={{ color: 'inherit', textDecoration: 'none' }}>Terms of Service</a>
            <a href="#" style={{ color: 'inherit', textDecoration: 'none' }}>Contact</a>
            <a href="#" style={{ color: 'inherit', textDecoration: 'none' }}>API</a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultsScreen;