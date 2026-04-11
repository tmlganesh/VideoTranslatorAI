import React, { useState } from 'react';
import ProgressBar from './components/ProgressBar';
import LandingScreen from './screens/LandingScreen';
import UploadScreen from './screens/UploadScreen';
import LanguageScreen from './screens/LanguageScreen';
import ProcessingScreen from './screens/ProcessingScreen';
import ResultsScreen from './screens/ResultsScreen';
import { apiUrl, API_BASE_URL } from './utils/api';

function App() {
  // Step navigation
  const [currentStep, setCurrentStep] = useState(1);

  // Form data
  const [videoUrl, setVideoUrl] = useState('');

  // Results
  const [transcriptionResult, setTranscriptionResult] = useState(null);
  const [translationResult, setTranslationResult] = useState(null);
  const [detectedLanguage, setDetectedLanguage] = useState(null);
  const [targetLanguageUsed, setTargetLanguageUsed] = useState(null);
  const [transcriptionStatus, setTranscriptionStatus] = useState(null);

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Navigation functions
  const nextStep = () => {
    if (currentStep < 5) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const startOver = () => {
    setCurrentStep(1);
    setVideoUrl('');
    setTranscriptionResult(null);
    setTranslationResult(null);
    setTargetLanguageUsed(null);
    setDetectedLanguage(null);
    setTranscriptionStatus(null);
    setError(null);
    setLoading(false);
  };

  // Transcription function
  const handleStartTranscription = async (targetLanguage = null, sourceLanguage = 'Auto-detect') => {
    setCurrentStep(4); // Move to processing screen
    setLoading(true);
    setError(null);

    try {
      // Transcribe from URL
      const response = await fetch(apiUrl('/api/transcribe/'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_url: videoUrl,
          target_language: targetLanguage && targetLanguage !== 'Same as Original (No Translation)' ? targetLanguage : null,
          source_language: sourceLanguage && sourceLanguage !== 'Auto-detect' ? sourceLanguage : null
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        const errorMessage = typeof errorData === 'object' ?
          (errorData.detail || JSON.stringify(errorData) || 'Failed to transcribe') :
          errorData;
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log('=== FRONTEND DEBUG ===');
      console.log('API base URL:', API_BASE_URL);
      console.log('Full response data:', data);
      console.log('Translation field:', data.translation);
      console.log('Target language field:', data.target_language);
      console.log('====================');

      setTranscriptionResult(data.transcription);
      setTranslationResult(data.translation);
      setTargetLanguageUsed(data.target_language);
      setTranscriptionStatus(data.status);
      setDetectedLanguage({
        name: data.detected_language,
        code: data.language_code
      });

      setCurrentStep(5); // Move to results screen
    } catch (err) {
      setError(err.message);
      console.error('Transcription error:', err);
      setCurrentStep(4); // Keep user on processing screen to show error and retry option
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    setError(null);
    setCurrentStep(3); // Go back to language selection
  };

  const renderCurrentScreen = () => {
    switch (currentStep) {
      case 1:
        return <LandingScreen onNext={nextStep} />;

      case 2:
        return (
          <UploadScreen
            videoUrl={videoUrl}
            setVideoUrl={setVideoUrl}
            onNext={nextStep}
            onPrev={prevStep}
          />
        );

      case 3:
        return (
          <LanguageScreen
            onNext={nextStep}
            onPrev={prevStep}
            onStartTranscription={handleStartTranscription}
          />
        );

      case 4:
        return (
          <ProcessingScreen
            error={error}
            onRetry={handleRetry}
          />
        );

      case 5:
        return (
          <ResultsScreen
            transcriptionResult={transcriptionResult}
            translationResult={translationResult}
            targetLanguage={targetLanguageUsed}
            detectedLanguage={detectedLanguage}
            transcriptionStatus={transcriptionStatus}
            onNewTranscription={startOver}
          />
        );

      default:
        return <LandingScreen onNext={nextStep} />;
    }
  };

  const appStyle = {
    minHeight: '100vh',
    background: '#f8fafc',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    width: '100%',
    margin: '0',
    padding: '0'
  };

  return (
    <div style={appStyle}>
      <main>
        {renderCurrentScreen()}
      </main>
    </div>
  );
}

export default App;