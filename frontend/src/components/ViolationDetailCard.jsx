import React from 'react';
import { Youtube, Search, CheckCircle } from 'lucide-react';

const ViolationDetailCard = ({ variant = 'main', violation = null }) => {
  // Variant 'main' for the big center card
  // Variant 'side' for the smaller one under Transcript

  if (!violation) {
    if (variant === 'main') {
      return (
        <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
           <CheckCircle color="var(--success)" size={48} style={{ marginBottom: '16px' }} />
           <h3 style={{ color: 'var(--success)' }}>All Clear</h3>
           <p style={{ color: 'var(--text-secondary)' }}>No specific violations to detail.</p>
        </div>
      );
    }
    return null;
  }
  
  const isHigh = violation.severity === 'high';

  if (variant === 'main') {
    return (
      <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div className="card-header" style={{ borderBottom: 'none', paddingBottom: 0 }}>
          <h3 style={{ fontSize: '1.2rem', color: '#1f2937' }}>Violation Details</h3>
        </div>
        
        <div className="card-body" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          
          <div style={{ backgroundColor: isHigh ? 'var(--danger-light)' : 'var(--warning-light)', border: `1px solid ${isHigh ? 'var(--danger-border)' : 'var(--warning-border)'}`, borderRadius: '8px', padding: '16px', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Youtube color={isHigh ? '#ef4444' : '#f59e0b'} size={24} />
              <h4 style={{ color: isHigh ? 'var(--danger)' : '#b45309', fontSize: '1.1rem', margin: 0, fontWeight: 600 }}>{violation.category || 'General Violation'}</h4>
            </div>
            {violation.timestamp && <p style={{ margin: '0 0 4px 0', fontSize: '0.9rem', fontWeight: 500 }}>Timestamp: {violation.timestamp}</p>}
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '20px', flex: 1 }}>
            <div>
              <h5 style={{ margin: '0 0 8px 0', fontSize: '1rem', color: '#1f2937' }}>Observation & Explanation</h5>
              <p style={{ margin: '0 0 12px 0', fontSize: '0.9rem', color: 'var(--text-primary)', whiteSpace: 'pre-wrap' }}>
                {violation.description}
              </p>
            </div>
            
            {/* Example Frame Box */}
            <div style={{ borderRadius: '8px', overflow: 'hidden', position: 'relative', border: '1px solid var(--border)', backgroundColor: '#000' }}>
               <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'rgba(255,255,255,0.3)' }}>
                  [Frame TBD]
               </div>
              <div style={{ 
                position: 'absolute', bottom: 0, left: 0, right: 0, 
                backgroundColor: 'rgba(0,0,0,0.6)', color: 'white', padding: '6px', textAlign: 'center', fontSize: '0.85rem', fontWeight: 500
              }}>
                Trigger Frame
              </div>
            </div>
          </div>
          
        </div>
      </div>
    );
  }

  // Side Variant (Under Transcript)
  return (
    <div className="card">
      <div className="card-header">
        <h4 style={{ margin: 0, fontSize: '1rem' }}>Violation Quick Details</h4>
      </div>
      <div className="card-body">
        <h5 style={{ color: isHigh ? 'var(--danger)' : '#b45309', fontSize: '1rem', margin: '0 0 12px 0' }}>{violation.category}</h5>
        
        {violation.timestamp && <p style={{ margin: '0 0 4px 0', fontSize: '0.9rem', color: 'var(--text-primary)' }}>Time: {violation.timestamp}</p>}
        
        <h6 style={{ margin: '12px 0 8px 0', fontSize: '0.95rem' }}>Description Snippet</h6>
        <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
           {violation.description?.substring(0, 100)}...
        </p>
      </div>
    </div>
  );
};

export default ViolationDetailCard;
