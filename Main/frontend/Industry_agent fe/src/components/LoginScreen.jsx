import React, { useState } from 'react';
import { Cpu, ShieldCheck, Key, User, ArrowRight, Info } from 'lucide-react';
import { apiClient } from '../api/client';

export const LoginScreen = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.login(username.trim(), password.trim());
      onLoginSuccess(data);
    } catch (err) {
      setError(err.message || "Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (usr, pwd) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.login(usr, pwd);
      onLoginSuccess(data);
    } catch (err) {
      setError(err.message || "Quick login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-screen-overlay">
      <div className="login-card-container animate-fade-in">
        {/* Card Header Logo */}
        <div className="login-card-header">
          <div className="login-logo-wrapper">
            <Cpu size={24} />
          </div>
          <h2 className="login-title">IndusIQ</h2>
          <p className="login-subtitle">Industrial Knowledge Intelligence Platform</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="login-form">
          {error && (
            <div className="login-error-box">
              <Info size={14} style={{ marginRight: '6px', flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          <div className="input-group-field">
            <label className="input-label-tag">Username</label>
            <div className="input-wrapper-inner">
              <User size={16} className="input-field-icon" />
              <input
                type="text"
                placeholder="Enter username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="login-text-input"
              />
            </div>
          </div>

          <div className="input-group-field" style={{ marginTop: '16px' }}>
            <label className="input-label-tag">Password</label>
            <div className="input-wrapper-inner">
              <Key size={16} className="input-field-icon" />
              <input
                type="password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="login-text-input"
              />
            </div>
          </div>

          <button type="submit" disabled={loading} className="login-submit-btn">
            {loading ? 'Authenticating...' : 'Sign In'}
            {!loading && <ArrowRight size={16} style={{ marginLeft: '8px' }} />}
          </button>
        </form>

        {/* Divider */}
        <div className="login-divider-row">
          <span className="login-divider-line"></span>
          <span className="login-divider-text">QUICK ACCESS SEEDED ACCOUNTS</span>
          <span className="login-divider-line"></span>
        </div>

        {/* Quick Seeding accounts card */}
        <div className="quick-access-grid">
          <div className="quick-login-card" onClick={() => handleQuickLogin('kannan', 'engineer123')}>
            <div className="quick-avatar engineer">ENG</div>
            <div className="quick-details">
              <div className="quick-name">R. Kannan</div>
              <div className="quick-role">Chief Engineer (All Access)</div>
            </div>
          </div>

          <div className="quick-login-card" onClick={() => handleQuickLogin('suriya', 'tech123')}>
            <div className="quick-avatar technician">TECH</div>
            <div className="quick-details">
              <div className="quick-name">Suriya</div>
              <div className="quick-role">Technician (Maintenance)</div>
            </div>
          </div>

          <div className="quick-login-card" onClick={() => handleQuickLogin('operator1', 'operator123')}>
            <div className="quick-avatar operator">OPE</div>
            <div className="quick-details">
              <div className="quick-name">Operator 1</div>
              <div className="quick-role">Operator (Safety & Telemetry)</div>
            </div>
          </div>
        </div>

        <div className="login-footer-disclaimer">
          <ShieldCheck size={12} style={{ marginRight: '4px', color: 'var(--text-muted)' }} />
          <span>Role-Based Access Control Active &bull; Secured session data</span>
        </div>
      </div>
    </div>
  );
};
