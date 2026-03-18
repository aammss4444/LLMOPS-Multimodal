import React from 'react';
import { AlertTriangle, CheckCircle, Info, FileText } from 'lucide-react';

const ResultsDisplay = ({ results }) => {
  if (!results) return null;

  const { final_status, compliance_issues = [], final_report } = results;

  const isPass = final_status?.toUpperCase() === 'PASS';

  return (
    <div className="glass-panel animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Level Status Card */}
      <div style={{
        padding: '24px',
        borderRadius: '12px',
        background: isPass ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
        border: `1px solid ${isPass ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
        display: 'flex',
        alignItems: 'center',
        gap: '20px'
      }}>
        {isPass ? (
          <CheckCircle size={48} color="var(--success)" />
        ) : (
          <AlertTriangle size={48} color="var(--error)" />
        )}
        
        <div>
          <h2 style={{ fontSize: '1.8rem', color: isPass ? 'var(--success)' : 'var(--error)', margin: '0 0 8px 0' }}>
            {isPass ? 'COMPLIANT' : 'NON-COMPLIANT'}
          </h2>
          <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
            {isPass 
              ? 'The provided media meets all audited brand and regulatory guidelines.' 
              : `Found ${compliance_issues.length} potential compliance issue(s) that require attention.`}
          </p>
        </div>
      </div>

      {/* Issues List */}
      {compliance_issues.length > 0 && (
        <div>
          <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={20} color="var(--warning)" /> Identified Issues
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {compliance_issues.map((issue, idx) => (
              <div key={idx} style={{
                background: 'rgba(15, 23, 42, 0.6)',
                borderLeft: `4px solid ${issue.severity === 'high' ? 'var(--error)' : 'var(--warning)'}`,
                padding: '16px',
                borderRadius: '0 8px 8px 0'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '1.1rem' }}>
                    {issue.category}
                  </span>
                  {issue.timestamp && (
                    <span style={{ fontSize: '0.85rem', color: 'var(--primary)', background: 'rgba(99, 102, 241, 0.1)', padding: '2px 8px', borderRadius: '4px' }}>
                      {issue.timestamp}
                    </span>
                  )}
                </div>
                <p style={{ color: 'var(--text-secondary)', margin: '0 0 12px 0', fontSize: '0.95rem' }}>
                  {issue.description}
                </p>
                <div style={{ display: 'inline-block', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700,
                     color: issue.severity === 'high' ? '#fca5a5' : '#fcd34d',
                     background: issue.severity === 'high' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                     padding: '4px 8px', borderRadius: '4px'
                }}>
                  Severity: {issue.severity || 'Medium'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Final Report */}
      {final_report && (
        <div style={{ marginTop: '12px' }}>
          <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={20} color="var(--primary)" /> Audit Summary Report
          </h3>
          <div style={{ 
            background: 'rgba(255, 255, 255, 0.03)', 
            padding: '24px', 
            borderRadius: '8px',
            border: '1px solid var(--glass-border)',
            whiteSpace: 'pre-wrap',
            color: 'var(--text-secondary)',
            fontSize: '0.95rem',
            lineHeight: 1.7
          }}>
            {final_report}
          </div>
        </div>
      )}

    </div>
  );
};

export default ResultsDisplay;
