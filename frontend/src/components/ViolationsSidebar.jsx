import React from 'react';
import { AlertTriangle, Youtube, CheckCircle } from 'lucide-react';

const ViolationsSidebar = ({ violations = [], activeIndex = 0, onSelectViolation }) => {
  if (violations.length === 0) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
        <h3 style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Violations Detected</h3>
        <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '32px', textAlign: 'center' }}>
          <CheckCircle size={48} color="var(--success)" style={{ marginBottom: '16px' }} />
          <h4 style={{ color: 'var(--success)', fontSize: '1.2rem', margin: '0 0 8px 0' }}>100% Compliant</h4>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: 0 }}>No policy violations were detected in this media payload.</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
      <h3 style={{ fontSize: '1.1rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>Violations Detected</h3>
      
      <div className="sidebar-grid" style={{ flex: 1 }}>
        {violations.map((v, idx) => {
          const isHigh = v.severity === 'high';
          const isActive = activeIndex === idx;

          return (
            <div 
              key={idx} 
              className="card" 
              style={{ 
                padding: '12px', 
                border: isActive ? `2px solid ${isHigh ? 'var(--danger)' : 'var(--warning)'}` : '1px solid var(--border)',
                cursor: 'pointer',
                transition: 'all 0.2s',
                backgroundColor: isActive ? (isHigh ? 'var(--danger-light)' : 'var(--warning-light)') : 'white'
              }}
              onClick={() => onSelectViolation(idx)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <AlertTriangle size={18} color={isHigh ? 'var(--danger)' : 'var(--warning)'} fill={isHigh ? 'var(--danger-light)' : 'var(--warning-light)'} />
                  <span style={{ fontWeight: 600, color: '#1f2937', fontSize: '0.95rem' }}>{v.category || "General Violation"}</span>
                </div>
                <button className="btn" style={{ 
                  padding: '4px 12px', fontSize: '0.75rem', 
                  backgroundColor: isHigh ? '#e57373' : '#ffb74d', color: 'white', borderRadius: '4px' 
                }}>
                  View
                </button>
              </div>
              
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '4px 0 8px 0', paddingLeft: '24px' }}>
                {v.timestamp ? `At ${v.timestamp}` : 'General Issue'} 
                <br />
                <span style={{ fontStyle: 'italic' }}>"{v.description?.substring(0, 50)}..."</span>
              </p>
              
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px', paddingLeft: '24px' }}>
                <Youtube size={14} color="#3b82f6" /> Severity: {v.severity?.toUpperCase() || "MEDIUM"}
              </div>
            </div>
          );
        })}
      </div>

      <div className="card" style={{ marginTop: 'auto', display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', backgroundColor: '#f9fafb' }}>
        <Youtube color="#ef4444" size={40} />
        <div>
          <h4 style={{ margin: '0 0 4px 0', fontSize: '1rem', color: '#1f2937' }}>YouTube Community Guidelines</h4>
          <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-muted)' }}>Analyzed via Gemini Knowledge Base</p>
        </div>
      </div>
    </div>
  );
};

export default ViolationsSidebar;
