import React from 'react';
import { CheckCircle2, Circle, Loader2, XCircle } from 'lucide-react';

const checkpoints = [
  { id: 'url_received', label: 'Initialization' },
  { id: 'video_download', label: 'Download Media' },
  { id: 'ffmpeg_audio_extract', label: 'Extract Audio' },
  { id: 'whisper_transcription', label: 'Transcription' },
  { id: 'ffmpeg_frame_extract', label: 'Extract Frames' },
  { id: 'paddleocr_extract', label: 'OCR Analysis' },
  { id: 'text_fusion', label: 'Data Fusion' },
  { id: 'audio_content_audit', label: 'Context Audit' },
  { id: 'visual_compliance_audit', label: 'Visual Check' },
];

const StatusTracker = ({ statusMap = {} }) => {
  if (Object.keys(statusMap).length === 0) return null;

  return (
    <div className="glass-panel animate-fade-in" style={{ marginBottom: '24px' }}>
      <h3 style={{ marginBottom: '20px', fontSize: '1.25rem' }}>Pipeline Status</h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {checkpoints.map((cp, idx) => {
          const state = statusMap[cp.id] || 'pending';
          
          let icon = <Circle size={20} color="var(--text-muted)" />;
          let color = 'var(--text-muted)';
          let bg = 'rgba(15, 23, 42, 0.4)';
          let border = '1px solid var(--glass-border)';

          if (state === 'completed') {
            icon = <CheckCircle2 size={20} color="var(--success)" />;
            color = 'var(--text-primary)';
            bg = 'rgba(16, 185, 129, 0.1)';
            border = '1px solid rgba(16, 185, 129, 0.3)';
          } else if (state === 'in_progress' || state === 'pending_active') {
            // we might not get "in_progress", but let's assume it could be inferred
            icon = <Loader2 size={20} color="var(--primary)" className="animate-spin" />;
            color = 'var(--primary)';
            bg = 'var(--primary-glow)';
            border = '1px solid var(--primary)';
          } else if (state === 'failed') {
            icon = <XCircle size={20} color="var(--error)" />;
            color = 'var(--error)';
            bg = 'rgba(239, 68, 68, 0.1)';
            border = '1px solid rgba(239, 68, 68, 0.3)';
          } else if (state === 'skipped') {
            icon = <Circle size={20} color="var(--warning)" />;
            color = 'var(--warning)';
          }

          // Let's create a simulated "active" state if the previous is completed and current is pending
          if (state === 'pending' && idx > 0 && statusMap[checkpoints[idx-1].id] === 'completed') {
            icon = <Loader2 size={20} color="var(--primary)" className="animate-spin" />;
            color = 'var(--primary)';
            bg = 'var(--primary-glow)';
            border = '1px solid var(--primary)';
          }

          // Special case: First item is active if everything is pending but we started
          if (state === 'pending' && idx === 0 && Object.keys(statusMap).length > 0) {
            icon = <Loader2 size={20} color="var(--primary)" className="animate-spin" />;
            color = 'var(--primary)';
            bg = 'var(--primary-glow)';
            border = '1px solid var(--primary)';
          }

          return (
            <div 
              key={cp.id} 
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '12px 16px',
                background: bg,
                border: border,
                borderRadius: '8px',
                transition: 'all 0.3s ease'
              }}
            >
              {icon}
              <span style={{ color, fontWeight: 500 }}>{cp.label}</span>
              {state === 'completed' && (
                <span style={{ marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--success)' }}>Done</span>
              )}
              {state === 'failed' && (
                <span style={{ marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--error)' }}>Failed</span>
              )}
            </div>
          );
        })}
      </div>
      <style>{`
        @keyframes spin { 100% { transform: rotate(360deg); } }
        .animate-spin { animation: spin 2s linear infinite; }
      `}</style>
    </div>
  );
};

export default StatusTracker;
