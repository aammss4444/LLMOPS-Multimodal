import React from 'react';
import { ShieldAlert, Play, Activity } from 'lucide-react';

const Header = () => {
  return (
    <header className="glass-panel" style={{ 
      marginBottom: '32px', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'space-between',
      padding: '16px 24px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{ 
          background: 'var(--primary-glow)', 
          padding: '10px', 
          borderRadius: '12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 15px var(--primary-glow)'
        }}>
          <ShieldAlert size={28} color="var(--primary)" />
        </div>
        <div>
          <h1 style={{ fontSize: '1.5rem', margin: 0 }}>
            Multimodal <span className="text-gradient">LLMOps</span>
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: 0 }}>
            Intelligent Media Compliance Auditor
          </p>
        </div>
      </div>
      
      <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
        <div className="flex-center" style={{ gap: '6px', fontSize: '0.85rem', color: 'var(--success)' }}>
          <Activity size={16} /> Backend Online
        </div>
      </div>
    </header>
  );
};

export default Header;
