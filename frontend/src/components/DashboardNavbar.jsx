import React from 'react';
import { Youtube, User, Settings, FileText, Upload } from 'lucide-react';

const DashboardNavbar = () => {
  return (
    <nav style={{ 
      backgroundColor: 'var(--header-bg)', 
      color: 'white', 
      padding: '12px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      boxShadow: 'var(--shadow-md)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <Youtube color="#ef4444" size={32} />
        <h1 style={{ fontSize: '1.25rem', margin: 0, fontWeight: 500, color: 'white' }}>
          QA Video Compliance
        </h1>
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '24px', fontSize: '0.9rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
          <User size={18} /> Admin
        </div>
      </div>
    </nav>
  );
};

export default DashboardNavbar;
