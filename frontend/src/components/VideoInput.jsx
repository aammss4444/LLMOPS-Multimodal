import React, { useState } from 'react';
import { Youtube, Hash, Search, Loader2 } from 'lucide-react';

const VideoInput = ({ onSubmit, isLoading }) => {
  const [url, setUrl] = useState('');
  const [campaignId, setCampaignId] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!url.trim() || !campaignId.trim()) return;
    onSubmit({ videoUrl: url.trim(), videoId: campaignId.trim() });
  };

  return (
    <div className="card animate-fade-in" style={{ maxWidth: '600px', margin: '60px auto', padding: '32px' }}>
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <div style={{ 
          width: '64px', height: '64px', borderRadius: '50%', backgroundColor: '#fef2f2', 
          display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px auto'
        }}>
          <Youtube color="#ef4444" size={32} />
        </div>
        <h2 style={{ margin: '0 0 8px 0', fontSize: '1.5rem', color: '#1f2937' }}>New Compliance Audit</h2>
        <p style={{ color: 'var(--text-secondary)', margin: 0, fontSize: '0.95rem' }}>
          Enter the YouTube URL and campaign identifier to begin processing multimodal content against policy guidelines.
        </p>
      </div>
      
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', fontWeight: 500 }}>
            YouTube Video URL
          </label>
          <div style={{ position: 'relative' }}>
            <Youtube size={18} color="var(--text-muted)" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
            <input 
              type="text" 
              placeholder="https://youtube.com/watch?v=..." 
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              disabled={isLoading}
              required
              style={{
                width: '100%', padding: '10px 10px 10px 40px', border: '1px solid var(--border)',
                borderRadius: '6px', fontSize: '1rem', outline: 'none', transition: 'border-color 0.2s'
              }}
              onFocus={(e) => e.target.style.borderColor = 'var(--primary)'}
              onBlur={(e) => e.target.style.borderColor = 'var(--border)'}
            />
          </div>
        </div>
        
        <div>
          <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.9rem', fontWeight: 500 }}>
            Campaign ID
          </label>
          <div style={{ position: 'relative' }}>
            <Hash size={18} color="var(--text-muted)" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
            <input 
              type="text" 
              placeholder="e.g. ad_campaign_001" 
              value={campaignId}
              onChange={(e) => setCampaignId(e.target.value)}
              disabled={isLoading}
              required
              style={{
                width: '100%', padding: '10px 10px 10px 40px', border: '1px solid var(--border)',
                borderRadius: '6px', fontSize: '1rem', outline: 'none', transition: 'border-color 0.2s'
              }}
              onFocus={(e) => e.target.style.borderColor = 'var(--primary)'}
              onBlur={(e) => e.target.style.borderColor = 'var(--border)'}
            />
          </div>
        </div>
        
        <button 
          type="submit" 
          className="btn btn-primary" 
          disabled={isLoading || !url.trim() || !campaignId.trim()}
          style={{ width: '100%', padding: '12px', fontSize: '1.05rem', marginTop: '8px', opacity: isLoading ? 0.7 : 1 }}
        >
          {isLoading ? (
            <><Loader2 size={18} className="animate-spin" /> Processing Media Pipeline...</>
          ) : (
            <><Search size={18} /> Start Pipeline Analysis</>
          )}
        </button>
      </form>
      <style>{`
        @keyframes spin { 100% { transform: rotate(360deg); } }
        .animate-spin { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  );
};

export default VideoInput;
