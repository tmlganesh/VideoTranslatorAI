import React, { useState } from 'react';
import { generateAccuracyReport, getAccuracyColor } from '../utils/accuracyCalculator';

const ResultsScreen = ({ transcriptionResult, translationResult, targetLanguage, detectedLanguage, onNewTranscription }) => {
  const [originalText, setOriginalText] = useState('');
  const [accuracyReport, setAccuracyReport] = useState(null);
  const [backendAccuracy, setBackendAccuracy] = useState(null);
  const [accuracyMode, setAccuracyMode] = useState('transcription'); // 'transcription' or 'translation'
  const [showLocalDetails, setShowLocalDetails] = useState(false);
  const [isCalculating, setIsCalculating] = useState(false);
  const [showAccuracySection, setShowAccuracySection] = useState(false);

  // Use actual transcription data or fallback (avoid using placeholder when empty/whitespace)
  const actualTranscription = (transcriptionResult && transcriptionResult.trim() !== "") ? transcriptionResult : `There was an idea stark knows this called the Avengers Initiative. The idea was to bring together a group of remarkable people, see if they could become something more.

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

  // Handle file upload for original text
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (file) {
      const text = await file.text();
      setOriginalText(text);
      setShowAccuracySection(true);
    }
  };

  // Calculate accuracy with loading animation
  const handleCalculateAccuracy = async () => {
    if (!originalText.trim()) {
      alert('Please paste or upload original text first');
      return;
    }

    const targetText = accuracyMode === 'translation' ? actualTranslation : actualTranscription;

    // Safety check
    if (!targetText) {
      alert('Selected target text is empty or unavailable.');
      return;
    }

    setIsCalculating(true);
    setBackendAccuracy(null);
    setAccuracyReport(null);

    // Debug: verify which texts are being compared
    try {
      console.log('[Accuracy Debug] Mode:', accuracyMode);
      console.log('[Accuracy Debug] Original (Reference):', originalText.slice(0, 50) + '...');
      console.log('[Accuracy Debug] Target (Predicted):', targetText.slice(0, 50) + '...');
    } catch { }

    try {
      // 1. Local Calculation (Immediate feedback fallback)
      try {
        const report = generateAccuracyReport(originalText, targetText);
        setAccuracyReport(report);
      } catch (localError) {
        console.error("Local accuracy calculation failed:", localError);
      }

      // 2. Backend Calculation (Authoritative)
      const res = await fetch('http://localhost:8000/api/evaluate-accuracy/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reference_text: originalText, predicted_text: targetText })
      });

      if (res.ok) {
        const data = await res.json();
        setBackendAccuracy(data);
      } else {
        console.warn("Backend evaluation failed, using local results only");
      }
    } catch (e) {
      console.error("Accuracy API error:", e);
    } finally {
      setIsCalculating(false);
    }
  };

  // Handle paste from clipboard
  const handlePasteText = async () => {
    try {
      const text = await navigator.clipboard.readText();
      setOriginalText(text);
      setShowAccuracySection(true);
    } catch (err) {
      alert('Failed to paste from clipboard');
    }
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

  // Accuracy Section Styles
  const accuracySectionStyle = {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    borderRadius: '12px',
    padding: '32px',
    color: 'white',
    marginBottom: '48px',
    boxShadow: '0 10px 30px rgba(102, 126, 234, 0.3)'
  };

  const accuracyHeaderStyle = {
    fontSize: '24px',
    fontWeight: '700',
    marginBottom: '24px',
    display: 'flex',
    alignItems: 'center',
    gap: '12px'
  };

  const uploadAreaStyle = {
    border: '2px dashed rgba(255, 255, 255, 0.5)',
    borderRadius: '8px',
    padding: '20px',
    textAlign: 'center',
    marginBottom: '20px',
    cursor: 'pointer',
    transition: 'all 0.3s ease',
    background: 'rgba(255, 255, 255, 0.1)'
  };

  const inputFileStyle = {
    display: 'none'
  };

  const textareaStyle = {
    width: '100%',
    minHeight: '120px',
    padding: '12px',
    borderRadius: '8px',
    border: '1px solid rgba(255, 255, 255, 0.3)',
    background: 'rgba(255, 255, 255, 0.1)',
    color: 'white',
    fontSize: '14px',
    lineHeight: '1.6',
    fontFamily: 'inherit',
    marginBottom: '16px',
    resize: 'vertical'
  };

  const textareaPlaceholder = {
    color: 'rgba(255, 255, 255, 0.6)'
  };

  const accuracyButtonsContainerStyle = {
    display: 'flex',
    gap: '12px',
    marginBottom: '20px',
    flexWrap: 'wrap'
  };

  const accuracyButtonStyle = {
    padding: '10px 20px',
    borderRadius: '8px',
    fontSize: '14px',
    fontWeight: '500',
    cursor: 'pointer',
    border: 'none',
    background: 'rgba(255, 255, 255, 0.2)',
    color: 'white',
    transition: 'all 0.3s ease',
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  };

  const calculateButtonStyle = {
    ...accuracyButtonStyle,
    background: 'rgba(255, 255, 255, 0.95)',
    color: '#667eea',
    fontWeight: '600'
  };

  const loadingSpinnerStyle = {
    display: 'inline-block',
    width: '20px',
    height: '20px',
    border: '3px solid rgba(255, 255, 255, 0.3)',
    borderTopColor: 'white',
    borderRadius: '50%',
    animation: 'spin 0.6s linear infinite'
  };

  const accuracyResultsStyle = {
    background: 'rgba(255, 255, 255, 0.15)',
    borderRadius: '8px',
    padding: '24px',
    marginTop: '20px'
  };

  const accuracyScoreStyle = (accuracy) => ({
    fontSize: '48px',
    fontWeight: '700',
    color: getAccuracyColor(accuracy),
    marginBottom: '8px',
    textShadow: '0 2px 4px rgba(0, 0, 0, 0.2)'
  });

  const accuracyLabelStyle = {
    fontSize: '16px',
    color: 'rgba(255, 255, 255, 0.9)',
    marginBottom: '20px'
  };

  const metricsGridStyle = {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '16px'
  };

  const metricCardStyle = {
    background: 'rgba(255, 255, 255, 0.1)',
    padding: '16px',
    borderRadius: '8px',
    textAlign: 'center'
  };

  const metricValueStyle = {
    fontSize: '24px',
    fontWeight: '600',
    marginBottom: '4px',
    color: '#fff'
  };

  const metricLabelStyle = {
    fontSize: '12px',
    color: 'rgba(255, 255, 255, 0.8)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px'
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
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        .accuracy-container {
          animation: slideIn 0.5s ease-out;
        }
        textarea::placeholder {
          color: rgba(255, 255, 255, 0.6);
        }
      `}</style>
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

        {/* Accuracy Section */}
        <div style={accuracySectionStyle} className="accuracy-container">
          <div style={accuracyHeaderStyle}>
            📊 Accuracy Logic Checker
          </div>

          <div style={{ marginBottom: '20px', background: 'rgba(255,255,255,0.1)', padding: '15px', borderRadius: '8px' }}>
            <label style={{ marginRight: '15px', fontWeight: '500', color: 'white' }}>Compare Reference Against:</label>
            <select
              value={accuracyMode}
              onChange={(e) => setAccuracyMode(e.target.value)}
              style={{ padding: '8px', borderRadius: '6px', border: 'none', background: 'white', color: '#1e293b' }}
            >
              <option value="transcription">Original Transcription</option>
              <option value="translation" disabled={!actualTranslation}>Translated Text {actualTranslation ? '' : '(Not Available)'}</option>
            </select>
            <p style={{ marginTop: '10px', fontSize: '13px', color: 'rgba(255,255,255,0.8)' }}>
              Select whether your uploaded text is a reference for the <strong>Transcription</strong> (Original Language) or the <strong>Translation</strong> (Target Language).
            </p>
          </div>

          {!showAccuracySection ? (
            <div>
              <p style={{ marginBottom: '20px', color: 'rgba(255, 255, 255, 0.9)', fontSize: '14px' }}>
                Upload or paste your reference text for evaluation
              </p>
              <div style={accuracyButtonsContainerStyle}>
                <label style={{ ...accuracyButtonStyle, cursor: 'pointer' }}>
                  <span>📤 Upload File</span>
                  <input
                    type="file"
                    style={inputFileStyle}
                    onChange={handleFileUpload}
                    accept=".txt"
                  />
                </label>
                <button
                  style={accuracyButtonStyle}
                  onClick={handlePasteText}
                >
                  📋 Paste Text
                </button>
              </div>
            </div>
          ) : (
            <div>
              <textarea
                value={originalText}
                onChange={(e) => setOriginalText(e.target.value)}
                placeholder="Your original text is here. You can edit it if needed..."
                style={textareaStyle}
              />
              <div style={accuracyButtonsContainerStyle}>
                <button
                  style={calculateButtonStyle}
                  onClick={handleCalculateAccuracy}
                  disabled={isCalculating}
                >
                  {isCalculating ? (
                    <>
                      <div style={loadingSpinnerStyle} />
                      Calculating Accuracy...
                    </>
                  ) : (
                    <>⚡ Calculate Accuracy</>
                  )}
                </button>
                <button
                  style={accuracyButtonStyle}
                  onClick={() => {
                    setOriginalText('');
                    setShowAccuracySection(false);
                    setAccuracyReport(null);
                    setBackendAccuracy(null);
                    setShowLocalDetails(false);
                    setIsCalculating(false);
                    // Optional: Reset mode? No, keep user preference.
                  }}
                >
                  ✕ Clear
                </button>
              </div>

              {/* Local metrics visibility toggle */}
              {!isCalculating && (accuracyReport || backendAccuracy) && (
                <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                  <button
                    style={{
                      padding: '8px 12px',
                      borderRadius: '8px',
                      border: '1px solid #e2e8f0',
                      background: showLocalDetails ? 'rgba(16,185,129,0.08)' : 'white',
                      color: '#0f172a'
                    }}
                    onClick={() => setShowLocalDetails(v => !v)}
                    disabled={!accuracyReport}
                    title={!accuracyReport ? 'Local metrics not available yet' : (showLocalDetails ? 'Hide Local Metrics' : 'Show Local Metrics')}
                  >{showLocalDetails ? 'Hide Local Metrics' : 'Show Local Metrics'}</button>
                </div>
              )}

              {/* Primary accuracy summary: prefer Backend WER, fallback to Local Similarity */}
              {!isCalculating && (accuracyReport || backendAccuracy) && (
                <div style={accuracyResultsStyle}>
                  {(() => {
                    // Priority: Backend Similarity > Backend Accuracy (clamped) > Local Similarity
                    const primaryAccuracy = backendAccuracy
                      ? (backendAccuracy.similarity_score ?? backendAccuracy.accuracy)
                      : (accuracyReport ? accuracyReport.overallAccuracy : null);

                    const primaryQuality = backendAccuracy
                      ? backendAccuracy.quality_level
                      : (accuracyReport ? accuracyReport.qualityLevel : null);

                    const sourceLabel = backendAccuracy
                      ? (backendAccuracy.similarity_score !== undefined ? 'AI Match Score' : 'Backend Accuracy')
                      : 'Local Similarity';

                    if (primaryAccuracy == null) return null;
                    return (
                      <>
                        <div style={accuracyScoreStyle(primaryAccuracy)}>
                          {primaryAccuracy.toFixed(2)}%
                        </div>
                        <div style={accuracyLabelStyle}>
                          {primaryQuality} · {sourceLabel}
                        </div>
                      </>
                    );
                  })()}
                </div>
              )}

              {/* Explanation Section */}
              {!isCalculating && (accuracyReport || backendAccuracy) && (
                <div style={{ marginTop: '20px', padding: '16px', borderRadius: '8px', background: 'rgba(0,0,0,0.2)', fontSize: '13px' }}>
                  <div style={{ fontWeight: 600, color: 'white', marginBottom: '8px' }}>ℹ️ How is this calculated?</div>
                  <div style={{ color: 'rgba(255,255,255,0.8)', lineHeight: '1.5' }}>
                    <p style={{ margin: '0 0 8px 0' }}>
                      <strong>Match Score (Similarity):</strong> Measures how closely the characters and words matches your reference text. 100% means a perfect match.
                    </p>
                    {backendAccuracy && (
                      <p style={{ margin: '0' }}>
                        <strong>WER (Word Error Rate):</strong> A strict technical metric measuring errors (substitutions, deletions, insertions). Lower is better. 0% WER = 100% Accuracy.
                      </p>
                    )}
                  </div>
                </div>
              )}

              {isCalculating && (
                <div style={accuracyResultsStyle}>
                  <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                    <div style={loadingSpinnerStyle} />
                    <p style={{ marginTop: '20px', color: 'rgba(255, 255, 255, 0.9)' }}>
                      Analyzing text accuracy...
                    </p>
                  </div>
                </div>
              )}

              {showLocalDetails && accuracyReport && !isCalculating && (
                <div style={accuracyResultsStyle}>
                  <div style={{ fontWeight: 600, fontSize: '16px', color: 'white', marginBottom: '8px' }}>Local Similarity Metrics</div>

                  <div style={metricsGridStyle}>
                    <div style={metricCardStyle}>
                      <div style={metricValueStyle}>
                        {accuracyReport.levenshteinScore.toFixed(2)}%
                      </div>
                      <div style={metricLabelStyle}>Character Accuracy</div>
                    </div>
                    <div style={metricCardStyle}>
                      <div style={metricValueStyle}>
                        {accuracyReport.wordScore.toFixed(2)}%
                      </div>
                      <div style={metricLabelStyle}>Vocabulary Match</div>
                    </div>
                    <div style={metricCardStyle}>
                      <div style={metricValueStyle}>
                        {accuracyReport.originalWordCount}
                      </div>
                      <div style={metricLabelStyle}>Original Words</div>
                    </div>
                    <div style={metricCardStyle}>
                      <div style={metricValueStyle}>
                        {accuracyReport.generatedWordCount}
                      </div>
                      <div style={metricLabelStyle}>Generated Words</div>
                    </div>
                  </div>

                  {accuracyReport.overallAccuracy < 75 && (
                    <div style={{
                      background: 'rgba(255, 255, 255, 0.1)',
                      padding: '16px',
                      borderRadius: '8px',
                      marginTop: '16px',
                      fontSize: '13px',
                      color: 'rgba(255, 255, 255, 0.9)',
                      lineHeight: '1.6'
                    }}>
                      💡 <strong>Tip:</strong> The accuracy score shows the similarity between your original text and the generated transcription. Lower scores may indicate areas that need correction.
                    </div>
                  )}
                </div>
              )}

              {backendAccuracy && !isCalculating && (
                <div style={{
                  background: 'rgba(17, 24, 39, 0.6)',
                  borderRadius: '12px',
                  padding: '24px',
                  marginTop: '16px',
                  border: '1px solid rgba(255,255,255,0.15)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                    <div style={{ fontWeight: 700, fontSize: '18px', color: 'white' }}>Backend WER Accuracy (FastAPI)</div>
                    <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.7)' }}>Lower WER = better</div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
                    <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: '10px', padding: '16px', border: '1px solid rgba(255,255,255,0.15)' }}>
                      <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px' }}>Match Score</div>
                      <div style={{ fontWeight: 700, fontSize: '20px', color: getAccuracyColor(backendAccuracy.similarity_score ?? backendAccuracy.accuracy) }}>
                        {(backendAccuracy.similarity_score ?? backendAccuracy.accuracy).toFixed(2)}%
                      </div>
                      <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.7)' }}>Sequence Match</div>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: '10px', padding: '16px', border: '1px solid rgba(255,255,255,0.15)' }}>
                      <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px' }}>WER Score</div>
                      <div style={{ fontWeight: 700, fontSize: '20px', color: '#0ea5e9' }}>{backendAccuracy.wer_percentage.toFixed(2)}%</div>
                      <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.7)' }}>Lower is better</div>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: '10px', padding: '16px', border: '1px solid rgba(255,255,255,0.15)' }}>
                      <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px' }}>Reference Words</div>
                      <div style={{ fontWeight: 700, fontSize: '20px', color: 'white' }}>{backendAccuracy.reference_words}</div>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: '10px', padding: '16px', border: '1px solid rgba(255,255,255,0.15)' }}>
                      <div style={{ color: 'rgba(255,255,255,0.8)', fontSize: '12px' }}>Predicted Words</div>
                      <div style={{ fontWeight: 700, fontSize: '20px', color: 'white' }}>{backendAccuracy.predicted_words}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
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
    </div >
  );
};

export default ResultsScreen;