import React, { useState } from 'react';

const TranscriptPanel = ({ transcript, ocrText }) => {
  const [activeTab, setActiveTab] = useState('transcript');
  
  // Format OCR text arrays into a readable block if needed
  const renderOcrContent = () => {
    if (!ocrText) return "No OCR text extracted from frames.";
    if (Array.isArray(ocrText)) {
      if (ocrText.length === 0) return "No OCR text extracted from frames.";
      return ocrText.map((block, i) => (
        <span key={i} style={{ display: 'block', marginBottom: '8px' }}>
          {typeof block === 'string' ? block : JSON.stringify(block)}
        </span>
      ));
    }
    return String(ocrText);
  };

  return (
    <div className="card mb-4" style={{ marginBottom: '16px' }}>
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ margin: 0, fontSize: '1rem', color: '#1f2937' }}>Extracted Text Payloads</h4>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          ALL MUST <div style={{ display: 'flex', gap: '3px' }}><div style={{ width: 4, height: 4, borderRadius: '50%', backgroundColor: '#9ca3af' }}></div><div style={{ width: 4, height: 4, borderRadius: '50%', backgroundColor: '#9ca3af' }}></div><div style={{ width: 4, height: 4, borderRadius: '50%', backgroundColor: '#9ca3af' }}></div></div>
        </div>
      </div>
      
      <div style={{ padding: '0 16px', borderBottom: '1px solid var(--border)', display: 'flex' }}>
        <button 
          onClick={() => setActiveTab('transcript')}
          style={{ 
            padding: '12px 16px', border: 'none', background: activeTab === 'transcript' ? 'var(--header-bg)' : 'transparent',
            color: activeTab === 'transcript' ? 'white' : 'var(--text-secondary)', fontWeight: 500, cursor: 'pointer',
            borderTopLeftRadius: '4px', borderTopRightRadius: '4px', marginTop: '12px', fontSize: '0.9rem'
          }}
        >
          Whisper Transcript
        </button>
        <button 
          onClick={() => setActiveTab('ocr')}
          style={{ 
             padding: '12px 16px', border: 'none', background: activeTab === 'ocr' ? 'var(--header-bg)' : 'transparent',
             color: activeTab === 'ocr' ? 'white' : 'var(--text-secondary)', fontWeight: 500, cursor: 'pointer',
            borderTopLeftRadius: '4px', borderTopRightRadius: '4px', marginTop: '12px', fontSize: '0.9rem'
          }}
        >
          PaddleOCR Text
        </button>
      </div>

      <div className="card-body" style={{ minHeight: '150px', maxHeight: '250px', overflowY: 'auto' }}>
        {activeTab === 'transcript' && (
          <p style={{ margin: 0, fontSize: '0.95rem', color: 'var(--text-primary)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
            {transcript || "No transcript returned by the backend."}
          </p>
        )}
        {activeTab === 'ocr' && (
          <div style={{ margin: 0, fontSize: '0.95rem', color: 'var(--text-primary)', lineHeight: 1.6 }}>
            {renderOcrContent()}
          </div>
        )}
      </div>
    </div>
  );
};

export default TranscriptPanel;
