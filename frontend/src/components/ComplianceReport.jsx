import React, { useMemo } from 'react';
import { Download, AlertTriangle, CheckCircle } from 'lucide-react';
import { PieChart, Pie, Cell, BarChart, Bar, ResponsiveContainer, Tooltip } from 'recharts';

const ComplianceReport = ({ results }) => {
  // Compute chart data dynamically based on the results prop
  
  const { compliance_issues = [], final_status } = results || {};
  
  const isPass = final_status?.toUpperCase() === 'PASS';
  
  // Calculate a mock dynamic score based on issues
  const calculateScore = () => {
    if (isPass) return 100;
    if (compliance_issues.length === 0) return 100;
    
    let penalty = 0;
    compliance_issues.forEach(i => {
      penalty += i.severity === 'high' ? 15 : 5;
    });
    return Math.max(0, 100 - penalty);
  };
  
  const complianceScore = calculateScore();
  
  const pieData = [
    { name: 'Compliant', value: complianceScore },
    { name: 'Violations', value: 100 - complianceScore }
  ];
  
  // Calculate Bar Chart distributions based on categories
  const barData = useMemo(() => {
    if (compliance_issues.length === 0) return [];
    
    const freqs = {};
    compliance_issues.forEach(issue => {
      const cat = issue.category || 'Other';
      freqs[cat] = (freqs[cat] || 0) + 1;
    });
    
    const data = Object.keys(freqs).map(cat => ({
      name: cat,
      value: freqs[cat],
      fill: freqs[cat] > 1 ? '#ef4444' : '#f59e0b'
    }));
    return data;
  }, [compliance_issues]);

  return (
    <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
      <div className="card-header" style={{ display: 'flex', alignItems: 'center', padding: '16px' }}>
        <h4 style={{ margin: 0, fontSize: '1.1rem', color: '#1f2937' }}>
          Compliance Score: <span style={{ color: isPass ? 'var(--success)' : 'var(--danger)', fontWeight: 700 }}>{complianceScore}%</span>
        </h4>
      </div>
      
      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '16px', flex: 1 }}>
        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--text-primary)' }}>
          Review Status: <span style={{ color: isPass ? 'var(--success)' : 'var(--danger)', fontWeight: 600 }}>{isPass ? 'Fully Compliant ✅' : 'Action Required ⚠️'}</span>
        </p>
        
        <div style={{ display: 'flex', gap: '16px', alignItems: 'stretch' }}>
          
          <div style={{ flex: 1 }}>
            <h5 style={{ margin: '0 0 8px 0', fontSize: '1rem', color: '#1f2937' }}>Violation Breakdown</h5>
            {compliance_issues.length > 0 ? (
              <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.9rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {barData.map((b, i) => (
                  <li key={i}>{b.name} (<strong style={{color: b.fill}}>{b.value}</strong>)</li>
                ))}
              </ul>
            ) : (
              <div style={{ color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.9rem' }}>
                <CheckCircle size={16} /> No violations
              </div>
            )}
          </div>
          
          <div style={{ flex: 1, border: '1px solid var(--border)', borderRadius: '8px', padding: '8px', position: 'relative' }}>
            <div style={{ display: 'flex', height: '100px' }}>
              
              {/* Mini Bar Chart */}
              <div style={{ flex: 1, height: '100%' }}>
                {barData.length > 0 && (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={barData} margin={{ top: 10, left: 0, right: 0, bottom: 0 }}>
                      <Tooltip cursor={{fill: 'rgba(0,0,0,0.05)'}} contentStyle={{fontSize: '12px', padding: '4px'}} />
                      <Bar dataKey="value" radius={[2, 2, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </div>
              
              {/* Mini Donut Chart */}
              <div style={{ width: '80px', height: '80px', position: 'relative', alignSelf: 'center' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      innerRadius={25}
                      outerRadius={35}
                      startAngle={90}
                      endAngle={-270}
                      dataKey="value"
                      stroke="none"
                    >
                      <Cell fill="#f9fafb" />
                      <Cell fill={isPass ? 'var(--success)' : '#f59e0b'} />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {complianceScore}%
                </div>
              </div>
            </div>
            
            <div style={{ position: 'absolute', left: 8, bottom: 8, right: 8, height: '1px', backgroundColor: 'var(--border)' }}></div>
            <div style={{ position: 'absolute', left: 8, bottom: 8, top: 8, width: '1px', backgroundColor: 'var(--border)' }}></div>
          </div>
        </div>
      </div>
      
      <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#f9fafb' }}>
        <button className="btn btn-outline" style={{ border: 'none', padding: '0', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
          <div style={{ backgroundColor: 'var(--primary)', color: 'white', padding: '6px', borderRadius: '50%', display: 'flex', alignItems: 'center' }}>
            <Download size={14} />
          </div>
          Download Final Report
        </button>
      </div>
    </div>
  );
};

export default ComplianceReport;
