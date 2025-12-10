import React from 'react';

const UploadScreen = ({ 
  uploadMethod, 
  setUploadMethod, 
  videoUrl, 
  setVideoUrl, 
  selectedFile, 
  setSelectedFile, 
  onNext, 
  onPrev 
}) => {
  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
  };

  const isValid = (uploadMethod === 'url' && videoUrl) || (uploadMethod === 'file' && selectedFile);

  const screenStyle = {
    minHeight: '100vh',
    background: '#f8fafc',
    padding: '24px'
  };

  const containerStyle = {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '48px 0'
  };

  const headerStyle = {
    textAlign: 'center',
    marginBottom: '48px'
  };

  const uploadOptionsStyle = {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '24px',
    margin: '32px 0'
  };

  const uploadOptionStyle = {
    background: '#f8fafc',
    border: '2px dashed #d1d5db',
    borderRadius: '12px',
    padding: '40px 32px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    textAlign: 'center',
    minHeight: '280px',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center'
  };

  const activeOptionStyle = {
    ...uploadOptionStyle,
    borderColor: '#3b82f6',
    background: '#f0f9ff',
    borderStyle: 'solid'
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
            Upload Your Video
          </h2>
          <p style={{ color: '#64748b', fontSize: '18px', lineHeight: '1.6', margin: '0' }}>
            Choose how you'd like to add your video content
          </p>
        </div>
        
        <div style={uploadOptionsStyle}>
          <div 
            style={uploadMethod === 'file' ? activeOptionStyle : uploadOptionStyle}
            onClick={() => setUploadMethod('file')}
          >
            <div style={{ fontSize: '48px', marginBottom: '24px', color: '#9ca3af' }}>⬆️</div>
            <h3 style={{ color: '#1e293b', marginBottom: '12px', fontSize: '18px', fontWeight: '600' }}>
              Upload Video File
            </h3>
            <p style={{ color: '#64748b', margin: '0 0 16px 0', fontSize: '14px', lineHeight: '1.5' }}>
              Drag and drop your video file here
            </p>
            <label 
              htmlFor="fileInput"
              style={{
                background: 'white',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                padding: '8px 16px',
                fontSize: '14px',
                color: '#374151',
                cursor: 'pointer',
                display: 'inline-block'
              }}
            >
              Browse Files
            </label>
            <p style={{ color: '#9ca3af', fontSize: '12px', margin: '16px 0 0 0' }}>
              Supports: MP4, MOV, AVI, MKV (Max 500MB)
            </p>
          </div>
          <div 
            style={uploadMethod === 'url' ? activeOptionStyle : uploadOptionStyle}
            onClick={() => setUploadMethod('url')}
          >
            <div style={{ fontSize: '48px', marginBottom: '24px', color: '#9ca3af' }}>�</div>
            <h3 style={{ color: '#1e293b', marginBottom: '12px', fontSize: '18px', fontWeight: '600' }}>
              Paste Video Link
            </h3>
            <p style={{ color: '#64748b', margin: '0 0 24px 0', fontSize: '14px', lineHeight: '1.5' }}>
              Enter a URL from YouTube, Vimeo, or other platforms
            </p>
            {uploadMethod === 'url' && (
              <div>
                <input
                  type="url"
                  value={videoUrl}
                  onChange={(e) => setVideoUrl(e.target.value)}
                  placeholder="https://youtube.com/watch?v=..."
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    fontSize: '14px',
                    border: '2px solid #e2e8f0',
                    borderRadius: '6px',
                    background: '#ffffff',
                    outline: 'none',
                    color: '#1e293b',
                    fontFamily: 'inherit'
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#3b82f6'}
                  onBlur={(e) => e.target.style.borderColor = '#e2e8f0'}
                />
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  marginTop: '16px'
                }}>
                  <button style={{
                    background: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '8px 12px',
                    fontSize: '14px',
                    cursor: 'pointer'
                  }}>
                    📋
                  </button>
                </div>
              </div>
            )}
            <p style={{ color: '#9ca3af', fontSize: '12px', margin: '16px 0 0 0' }}>
              YouTube, Vimeo, Dailymotion supported
            </p>
          </div>
        </div>
        
        {uploadMethod === 'file' && selectedFile && (
          <div style={{ textAlign: 'center', marginTop: '24px', padding: '16px', background: '#f0f9ff', borderRadius: '8px' }}>
            <p style={{ color: '#1e293b', margin: '0', fontSize: '14px' }}>
              <strong>Selected:</strong> {selectedFile.name}
            </p>
            <p style={{ color: '#64748b', margin: '8px 0 0 0', fontSize: '12px' }}>
              Size: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
        )}
        
        <input
          type="file"
          id="fileInput"
          onChange={handleFileChange}
          accept="video/*,audio/*"
          style={{ display: 'none' }}
        />
        
        <div style={{ textAlign: 'center', marginTop: '48px' }}>
          <button 
            style={{
              padding: '16px 48px',
              fontSize: '16px',
              fontWeight: '600',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              background: isValid ? '#8b5cf6' : '#d1d5db',
              color: 'white',
              transition: 'all 0.2s ease'
            }}
            onClick={onNext}
            disabled={!isValid}
          >
            Proceed
          </button>
        </div>
      </div>
    </div>
  );
};

export default UploadScreen;