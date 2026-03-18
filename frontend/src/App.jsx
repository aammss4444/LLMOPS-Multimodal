import React, { useState } from 'react';
import axios from 'axios';
import DashboardNavbar from './components/DashboardNavbar';
import VideoPlayerSection from './components/VideoPlayerSection';
import ViolationsSidebar from './components/ViolationsSidebar';
import ViolationDetailCard from './components/ViolationDetailCard';
import TranscriptPanel from './components/TranscriptPanel';
import ComplianceReport from './components/ComplianceReport';
import VideoInput from './components/VideoInput';
import { Download, AlertTriangle, AlertCircle } from 'lucide-react';

const API_BASE_URL = 'http://127.0.0.1:8000';

function App() {
  const [appState, setAppState] = useState('idle'); // 'idle' | 'loading' | 'success' | 'error'
  const [errorMsg, setErrorMsg] = useState(null);
  const [auditResults, setAuditResults] = useState(null);
  const [activeVideoUrl, setActiveVideoUrl] = useState('');
  
  // Lift active violation state so clicking a sidebar item updates the detail cards
  const [activeViolationIndex, setActiveViolationIndex] = useState(0);

  const handleAuditSubmit = async ({ videoUrl, videoId }) => {
    setAppState('loading');
    setErrorMsg(null);
    setAuditResults(null);
    setActiveVideoUrl(videoUrl);
    setActiveViolationIndex(0);

    try {
      const response = await axios.post(`${API_BASE_URL}/audit`, {
        video_url: videoUrl,
        video_id: videoId
      });

      const data = response.data;
      if (data.status === 'success' && data.results) {
        setAuditResults(data.results);
        setAppState('success');
      } else {
        setErrorMsg('The audit failed to return successful results.');
        setAppState('error');
      }
    } catch (err) {
      console.error("API call failed:", err);
      setErrorMsg(err.response?.data?.detail || err.message || 'An error occurred connecting to the backend API.');
      setAppState('error');
    }
  };

  const currentViolation = auditResults?.compliance_issues?.[activeViolationIndex] || null;
  const totalViolations = auditResults?.compliance_issues?.length || 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh', backgroundColor: 'var(--bg-color)' }}>
      <DashboardNavbar />
      
      {appState === 'idle' && (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <VideoInput onSubmit={handleAuditSubmit} isLoading={false} />
        </div>
      )}

      {appState === 'loading' && (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <VideoInput onSubmit={() => {}} isLoading={true} />
        </div>
      )}

      {appState === 'error' && (
        <div style={{ flex: 1, padding: '40px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div className="card" style={{ maxWidth: '600px', padding: '24px', backgroundColor: 'var(--danger-light)', borderColor: 'var(--danger-border)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--danger)', marginBottom: '16px' }}>
              <AlertCircle size={32} />
              <h3 style={{ margin: 0 }}>Processing Failed</h3>
            </div>
            <p style={{ margin: '0 0 16px 0', color: 'var(--text-primary)' }}>{errorMsg}</p>
            <button className="btn btn-primary" onClick={() => setAppState('idle')}>Try Again</button>
          </div>
        </div>
      )}

      {appState === 'success' && auditResults && (
        <>
          {/* Main Grid matching the mockup */}
          <div className="dashboard-grid animate-fade-in" style={{ flex: 1, paddingBottom: 0 }}>
            
            {/* Left Column (Main Video & Detailed Card) */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              
              <VideoPlayerSection videoUrl={activeVideoUrl} />
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px', flex: 1 }}>
                {/* Sidebar list inside left column */}
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <ViolationsSidebar 
                    violations={auditResults.compliance_issues || []} 
                    activeIndex={activeViolationIndex}
                    onSelectViolation={setActiveViolationIndex}
                  />
                </div>
                
                {/* Main Details Card */}
                <div>
                  <ViolationDetailCard variant="main" violation={currentViolation} />
                </div>
              </div>
              
            </div>

            {/* Right Column (Transcript & Reporting) */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <TranscriptPanel 
                transcript={auditResults.transcript} 
                ocrText={auditResults.ocr_text} 
              />
              <ViolationDetailCard variant="side" violation={currentViolation} />
              <ComplianceReport results={auditResults} />
            </div>

          </div>

          {/* Bottom Action Bar */}
          <div style={{ 
            backgroundColor: 'var(--header-bg)', 
            color: 'white', 
            padding: '12px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '24px',
            marginTop: '24px'
          }}>
            <button className="btn" style={{ backgroundColor: 'rgba(255,255,255,0.1)', color: 'white', border: '1px solid rgba(255,255,255,0.2)' }}>
              <Download size={16} /> Download Guidelines
            </button>
            <span style={{ color: 'rgba(255,255,255,0.3)' }}>|</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'white' }}>
              <AlertTriangle color={totalViolations > 0 ? "var(--danger)" : "var(--success)"} size={18} fill={totalViolations > 0 ? "var(--danger-light)" : "var(--success-light)"} />
              <span style={{ fontSize: '0.95rem' }}>Review Status: <strong style={{ color: 'white' }}>{totalViolations} Violations</strong></span>
            </div>
            <button className="btn" style={{ backgroundColor: '#f9fafb', color: 'var(--header-bg)' }}>
              <Download size={16} /> Download Report
            </button>
          </div>
        </>
      )}

    </div>
  );
}

export default App;
