import React, { createContext, useContext, useState, useCallback, useRef } from 'react';
import { CheckCircle2, XCircle, Info, AlertTriangle, X } from 'lucide-react';

/* ─── Context ─── */
const ToastContext = createContext(null);

/* ─── Hook ─── */
export const useToast = () => {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    // Graceful no-op if called outside provider (prevents silent crash)
    return {
      success: () => {},
      error: () => {},
      info: () => {},
      warning: () => {},
    };
  }
  return ctx;
};

/* ─── Toast Item Component ─── */
const ICONS = {
  success: <CheckCircle2 size={16} />,
  error: <XCircle size={16} />,
  info: <Info size={16} />,
  warning: <AlertTriangle size={16} />,
};

const COLORS = {
  success: {
    icon: 'var(--emerald-primary)',
    border: 'rgba(16,185,129,0.35)',
    bg: 'rgba(16,185,129,0.08)',
    bar: 'var(--emerald-primary)',
  },
  error: {
    icon: 'var(--rose-primary)',
    border: 'rgba(244,63,94,0.35)',
    bg: 'rgba(244,63,94,0.08)',
    bar: 'var(--rose-primary)',
  },
  info: {
    icon: 'var(--cyan-primary)',
    border: 'rgba(6,182,212,0.35)',
    bg: 'rgba(6,182,212,0.08)',
    bar: 'var(--cyan-primary)',
  },
  warning: {
    icon: 'var(--amber-primary)',
    border: 'rgba(245,158,11,0.35)',
    bg: 'rgba(245,158,11,0.08)',
    bar: 'var(--amber-primary)',
  },
};

const ToastItem = ({ toast, onDismiss }) => {
  const c = COLORS[toast.type] || COLORS.info;
  return (
    <div
      className="toast-item animate-slide-in-right"
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        padding: '14px 16px',
        background: 'var(--bg-surface-elevated)',
        border: `1px solid ${c.border}`,
        borderRadius: 'var(--radius-md)',
        boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
        minWidth: '300px',
        maxWidth: '420px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Progress bar */}
      <div
        className="toast-progress-bar"
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          height: '2px',
          background: c.bar,
          animation: `toast-shrink ${toast.duration}ms linear forwards`,
        }}
      />

      {/* Icon */}
      <div style={{ color: c.icon, flexShrink: 0, marginTop: '1px' }}>
        {ICONS[toast.type]}
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        {toast.title && (
          <div style={{
            fontSize: '13px',
            fontWeight: 700,
            color: '#ffffff',
            marginBottom: '2px',
            fontFamily: 'var(--font-display)',
          }}>
            {toast.title}
          </div>
        )}
        {toast.message && (
          <div style={{
            fontSize: '12px',
            color: 'var(--text-secondary)',
            lineHeight: '1.5',
            wordBreak: 'break-word',
          }}>
            {toast.message}
          </div>
        )}
      </div>

      {/* Dismiss */}
      <button
        onClick={() => onDismiss(toast.id)}
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--text-muted)',
          cursor: 'pointer',
          padding: '0',
          flexShrink: 0,
          display: 'flex',
          alignItems: 'center',
          transition: 'color 0.15s',
        }}
        onMouseEnter={e => e.currentTarget.style.color = '#ffffff'}
        onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
      >
        <X size={14} />
      </button>
    </div>
  );
};

/* ─── Provider ─── */
export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);
  const counterRef = useRef(0);

  const dismiss = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const addToast = useCallback((type, title, message, duration = 4500) => {
    const id = `toast-${++counterRef.current}`;
    setToasts(prev => [...prev.slice(-4), { id, type, title, message, duration }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
  }, []);

  const ctx = {
    success: (title, message, duration) => addToast('success', title, message, duration),
    error: (title, message, duration) => addToast('error', title, message, duration),
    info: (title, message, duration) => addToast('info', title, message, duration),
    warning: (title, message, duration) => addToast('warning', title, message, duration),
  };

  return (
    <ToastContext.Provider value={ctx}>
      {children}

      {/* Toast Container */}
      <div
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          zIndex: 9999,
          pointerEvents: 'none',
        }}
      >
        {toasts.map(t => (
          <div key={t.id} style={{ pointerEvents: 'auto' }}>
            <ToastItem toast={t} onDismiss={dismiss} />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

export default ToastProvider;
