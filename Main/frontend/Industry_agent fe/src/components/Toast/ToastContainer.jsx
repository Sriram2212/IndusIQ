import React from 'react';
import { CheckCircle2, AlertCircle, Info, AlertTriangle, Loader2, X } from 'lucide-react';

export const ToastContainer = ({ toasts, onDismiss }) => {
  if (!toasts || toasts.length === 0) return null;

  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 size={18} style={{ color: 'var(--emerald-primary)', flexShrink: 0 }} />;
      case 'error':
        return <AlertCircle size={18} style={{ color: 'var(--rose-primary)', flexShrink: 0 }} />;
      case 'warning':
        return <AlertTriangle size={18} style={{ color: 'var(--amber-primary)', flexShrink: 0 }} />;
      case 'loading':
        return <Loader2 size={18} className="animate-spin" style={{ color: 'var(--cyan-primary)', flexShrink: 0 }} />;
      default:
        return <Info size={18} style={{ color: 'var(--cyan-primary)', flexShrink: 0 }} />;
    }
  };

  const getBorderColor = (type) => {
    switch (type) {
      case 'success':
        return 'rgba(16, 185, 129, 0.4)';
      case 'error':
        return 'rgba(244, 63, 94, 0.4)';
      case 'warning':
        return 'rgba(245, 158, 11, 0.4)';
      case 'loading':
        return 'rgba(6, 182, 212, 0.4)';
      default:
        return 'rgba(6, 182, 212, 0.4)';
    }
  };

  const getAccentColor = (type) => {
    switch (type) {
      case 'success':
        return 'var(--emerald-primary)';
      case 'error':
        return 'var(--rose-primary)';
      case 'warning':
        return 'var(--amber-primary)';
      case 'loading':
        return 'var(--cyan-primary)';
      default:
        return 'var(--cyan-primary)';
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: '20px',
        right: '24px',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        maxWidth: '420px',
        width: 'calc(100vw - 48px)',
        pointerEvents: 'none'
      }}
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          style={{
            pointerEvents: 'auto',
            background: 'rgba(16, 20, 26, 0.94)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
            border: `1px solid ${getBorderColor(toast.type)}`,
            boxShadow: `0 10px 30px rgba(0, 0, 0, 0.5), 0 0 15px ${getBorderColor(toast.type)}`,
            borderRadius: 'var(--radius-md, 8px)',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px',
            animation: 'toastSlideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards',
            position: 'relative',
            overflow: 'hidden'
          }}
        >
          {/* Top Progress bar indicator */}
          {toast.duration > 0 && (
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                height: '3px',
                width: '100%',
                background: getAccentColor(toast.type),
                animation: `toastProgress ${toast.duration}ms linear forwards`,
                transformOrigin: 'left'
              }}
            />
          )}

          <div style={{ marginTop: '2px' }}>{getIcon(toast.type)}</div>

          <div style={{ flex: 1, minWidth: 0 }}>
            {toast.title && (
              <div
                style={{
                  fontSize: '13px',
                  fontWeight: 600,
                  color: '#ffffff',
                  marginBottom: '2px',
                  letterSpacing: '0.01em'
                }}
              >
                {toast.title}
              </div>
            )}
            {toast.message && (
              <div
                style={{
                  fontSize: '12px',
                  color: 'var(--text-secondary, #94a3b8)',
                  lineHeight: '1.4',
                  wordBreak: 'break-word'
                }}
              >
                {toast.message}
              </div>
            )}
          </div>

          <button
            onClick={() => onDismiss(toast.id)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted, #64748b)',
              cursor: 'pointer',
              padding: '2px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '4px',
              transition: 'color 0.2s',
              marginTop: '1px'
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#ffffff')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted, #64748b)')}
            title="Dismiss notification"
          >
            <X size={14} />
          </button>
        </div>
      ))}

      <style>{`
        @keyframes toastSlideIn {
          from {
            transform: translateX(100%) scale(0.95);
            opacity: 0;
          }
          to {
            transform: translateX(0) scale(1);
            opacity: 1;
          }
        }
        @keyframes toastProgress {
          from {
            transform: scaleX(1);
          }
          to {
            transform: scaleX(0);
          }
        }
      `}</style>
    </div>
  );
};
