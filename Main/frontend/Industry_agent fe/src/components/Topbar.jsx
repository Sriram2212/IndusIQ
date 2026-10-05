import React from 'react';
import { Cpu, LogOut } from 'lucide-react';

export const Topbar = ({ 
  userRole = "engineer", 
  fullName = "Guest",
  isOnline = false,
  onLogout,
  onToggleSidebar
}) => {
  // Format role string for cleaner representation
  const formattedRole = userRole.charAt(0).toUpperCase() + userRole.slice(1);

  return (
    <header className="topbar-header">
      {/* Brand Identification */}
      <div className="topbar-brand" style={{ gap: '12px' }}>
        <button 
          onClick={onToggleSidebar}
          title="Toggle Sidebar"
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            padding: '4px',
            transition: 'color 0.2s',
            outline: 'none'
          }}
          onMouseEnter={(e) => e.currentTarget.style.color = '#ffffff'}
          onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-secondary)'}
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            width="18" 
            height="18" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2" 
            strokeLinecap="round" 
            strokeLinejoin="round"
          >
            <line x1="4" x2="20" y1="12" y2="12"/>
            <line x1="4" x2="20" y1="6" y2="6"/>
            <line x1="4" x2="20" y1="18" y2="18"/>
          </svg>
        </button>

        <div className="brand-icon-wrapper">
          <Cpu size={18} />
        </div>
        <div className="brand-title-group">
          <span className="brand-title">IndusIQ</span>
          <span className="brand-badge">LANGGRAPH ORCHESTRATED</span>
          {/* Live backend status dot */}
          <span title={isOnline ? 'Backend Online' : 'Backend Offline'} style={{
            display: 'inline-flex', alignItems: 'center', gap: '5px',
            fontSize: '10px', fontFamily: 'var(--font-mono)',
            color: isOnline ? 'var(--emerald-primary)' : 'var(--rose-primary)',
            background: isOnline ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
            border: `1px solid ${isOnline ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
            padding: '2px 8px', borderRadius: '20px'
          }}>
            <span style={{
              width: '6px', height: '6px', borderRadius: '50%',
              background: isOnline ? 'var(--emerald-primary)' : 'var(--rose-primary)',
              boxShadow: isOnline ? '0 0 6px var(--emerald-primary)' : '0 0 6px var(--rose-primary)',
              display: 'inline-block'
            }} />
            {isOnline ? 'ONLINE' : 'OFFLINE'}
          </span>
        </div>
      </div>

      {/* Right Telemetry & Controls */}
      <div className="topbar-actions">
        {/* User profile with Full Name */}
        <div className="status-badge" style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
          <span>{fullName}</span>
        </div>

        {/* Role Display Badge (Static view, dropdown option removed) */}
        <div className="user-profile-badge" style={{ padding: '4px 12px 4px 6px', gap: '8px' }}>
          <div className="avatar-circle" style={{
            width: '26px',
            height: '26px',
            background: userRole === 'technician' ? 'linear-gradient(135deg, var(--cyan-primary), var(--emerald-primary))' :
                        userRole === 'operator' ? 'linear-gradient(135deg, var(--rose-primary), var(--amber-primary))' :
                        'linear-gradient(135deg, var(--violet-primary), var(--cyan-primary))'
          }}>
            {userRole.slice(0, 3).toUpperCase()}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', textAlign: 'left' }}>
            <span style={{ fontSize: '9px', color: 'var(--text-muted)', fontWeight: 700, letterSpacing: '0.05em', lineHeight: 1 }}>SYSTEM CLEARANCE</span>
            <span style={{
              color: '#ffffff',
              fontSize: '12px',
              fontWeight: 700,
              padding: '2px 0 0 0',
              margin: 0
            }}>
              {formattedRole}
            </span>
          </div>
        </div>

        {/* Log Out Button */}
        <button 
          onClick={onLogout} 
          title="Sign Out"
          style={{
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-base)',
            borderRadius: '50%',
            width: '32px',
            height: '32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.color = 'var(--rose-primary)'}
          onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
        >
          <LogOut size={14} />
        </button>
      </div>
    </header>
  );
};
