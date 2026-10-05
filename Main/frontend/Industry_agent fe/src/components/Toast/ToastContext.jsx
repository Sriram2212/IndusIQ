import React, { createContext, useContext, useState, useCallback } from 'react';
import { ToastContainer } from './ToastContainer';

const ToastContext = createContext(null);

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const show = useCallback(({ type = 'info', title, message, duration = 4500 }) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
    const newToast = { id, type, title, message, duration };

    setToasts((prev) => [...prev, newToast]);

    if (duration > 0) {
      setTimeout(() => {
        dismiss(id);
      }, duration);
    }

    return id;
  }, [dismiss]);

  const success = useCallback((title, message, duration) => {
    return show({ type: 'success', title, message, duration });
  }, [show]);

  const error = useCallback((title, message, duration) => {
    return show({ type: 'error', title, message, duration: duration || 6000 });
  }, [show]);

  const info = useCallback((title, message, duration) => {
    return show({ type: 'info', title, message, duration });
  }, [show]);

  const warning = useCallback((title, message, duration) => {
    return show({ type: 'warning', title, message, duration });
  }, [show]);

  const loading = useCallback((title, message) => {
    return show({ type: 'loading', title, message, duration: 0 });
  }, [show]);

  return (
    <ToastContext.Provider value={{ show, success, error, info, warning, loading, dismiss, toasts }}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
};

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};
