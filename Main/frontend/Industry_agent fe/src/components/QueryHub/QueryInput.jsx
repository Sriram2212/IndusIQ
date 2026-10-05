import React, { useState, useEffect, useMemo } from 'react';
import { Search, Sparkles, CornerDownLeft, Loader2, Zap, FlaskConical, Wrench } from 'lucide-react';

const SUGGESTION_ICONS = [Zap, FlaskConical, Wrench, Sparkles];

export const QueryInput = ({ 
  onSearch, 
  loading, 
  currentQuery, 
  documents = [], 
  assets = [] 
}) => {
  const [inputVal, setInputVal] = useState('');

  // Sync inputVal only when currentQuery is externally set (e.g. asset click)
  // Don't overwrite user typing
  useEffect(() => {
    if (currentQuery && currentQuery !== inputVal) {
      setInputVal(currentQuery);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentQuery]);

  // Generate dynamic investigation suggestions from real ingested documents & assets
  const dynamicSuggestions = useMemo(() => {
    const list = [];
    if (assets && assets.length > 0) {
      assets.slice(0, 2).forEach(asset => {
        const name = asset.name || asset.id;
        list.push(`What is the operational status of ${name}?`);
      });
    }
    if (documents && documents.length > 0) {
      documents.slice(0, 2).forEach(doc => {
        const name = doc.name || doc.filename;
        if (name) {
          list.push(`Summarize key findings in ${name}`);
        }
      });
    }
    // Always include fallback suggestions if not enough
    if (list.length < 3) {
      list.push('What are the recent maintenance issues across all equipment?');
      list.push('Identify equipment with abnormal vibration readings');
    }
    return list.slice(0, 4);
  }, [documents, assets]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputVal.trim() && !loading) {
      onSearch(inputVal.trim());
      setInputVal(''); // Clear after submit
    }
  };

  const handleKeyDown = (e) => {
    // Ctrl+Enter or Cmd+Enter to submit
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleSelectPreset = (preset) => {
    setInputVal(preset);
    onSearch(preset);
    setInputVal('');
  };

  return (
    <div className="query-hero-card">
      <div className="query-hero-eyebrow">
        <Sparkles size={14} />
        <span>Unified Industrial Intelligence Query</span>
        <span style={{
          marginLeft: 'auto',
          fontSize: '10px',
          fontFamily: 'var(--font-mono)',
          color: 'var(--text-muted)',
          padding: '2px 8px',
          background: 'var(--bg-surface-elevated)',
          borderRadius: 'var(--radius-pill)',
          border: '1px solid var(--border-subtle)'
        }}>
          ⌃ Enter to send
        </span>
      </div>

      <form className="query-input-form" onSubmit={handleSubmit}>
        <Search className="query-search-icon" />
        <input 
          type="text"
          className="query-input-field"
          placeholder="Ask anything across work orders, OEM manuals, vibration data, shift logs, SOPs..."
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          autoFocus
        />
        {inputVal.length > 0 && (
          <span style={{
            fontSize: '10px',
            fontFamily: 'var(--font-mono)',
            color: 'var(--text-muted)',
            marginRight: '8px',
            flexShrink: 0
          }}>
            {inputVal.length}
          </span>
        )}
        <button 
          type="submit" 
          className="query-submit-btn"
          disabled={loading || !inputVal.trim()}
        >
          {loading ? (
            <>
              <Loader2 size={14} className="animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <span>Investigate</span>
              <CornerDownLeft size={13} />
            </>
          )}
        </button>
      </form>

      {/* Dynamic Investigation Suggestions */}
      <div className="preset-prompts-row">
        <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', flexShrink: 0 }}>
          SUGGESTED:
        </span>
        {dynamicSuggestions.map((suggestion, idx) => {
          const Icon = SUGGESTION_ICONS[idx % SUGGESTION_ICONS.length];
          return (
            <button
              key={idx}
              type="button"
              className="preset-chip-btn"
              onClick={() => handleSelectPreset(suggestion)}
              disabled={loading}
            >
              <Icon size={10} style={{ opacity: 0.7 }} />
              <span>{suggestion}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
