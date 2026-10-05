import React from 'react';
import { 
  FileText, 
  Network, 
  CheckCircle2, 
  ExternalLink, 
  Layers, 
  Database,
  ShieldAlert,
  GitCommit
} from 'lucide-react';

export const EvidenceTrace = ({ sources = [], graphContext = [], highlightedDoc }) => {
  return (
    <aside className="trace-panel-aside">
      <div className="trace-panel-header">
        <div className="trace-panel-title">
          <Layers size={16} style={{ color: 'var(--amber-primary)' }} />
          <span>Evidence Trace & Audit</span>
        </div>
        <p className="trace-panel-subtitle">
          Every verified source and graph triple backing this response
        </p>
      </div>

      {/* Sources List */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '10px' }}>
          DOCUMENT CHUNKS ({sources.length})
        </div>

        {sources.length === 0 ? (
          <div style={{ padding: '16px', background: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', color: 'var(--text-muted)', fontSize: '12px' }}>
            No document chunks linked yet.
          </div>
        ) : (
          sources.map((src, idx) => {
            const isGraph = src.type === 'graph';
            const docName = src.document || src.name || 'Document Chunk';
            const isHighlighted = highlightedDoc && docName.toLowerCase().includes(highlightedDoc.toLowerCase());

            return (
              <div 
                key={idx} 
                className="trace-source-card animate-fade-in"
                style={{
                  borderColor: isHighlighted ? 'var(--amber-primary)' : 'var(--border-base)',
                  boxShadow: isHighlighted ? '0 0 14px var(--amber-glow)' : 'none'
                }}
              >
                <div className="source-card-top">
                  <span className="source-type-pill">
                    {isGraph ? <Network size={12} /> : <FileText size={12} />}
                    <span>{isGraph ? 'KNOWLEDGE GRAPH' : 'DOCUMENT CHUNK'}</span>
                  </span>
                  {src.verified && (
                    <span className="source-verified-badge">
                      <CheckCircle2 size={10} style={{ display: 'inline', marginRight: '3px' }} />
                      VERIFIED
                    </span>
                  )}
                </div>

                <div className="source-title">{docName}</div>
                <div className="source-detail">{src.detail || 'Context extracted during hybrid retrieval.'}</div>

                <div className="source-meta-bar">
                  <span>{src.section || (src.page ? `Page ${src.page}` : 'Verified Fact')}</span>
                  <span style={{ color: 'var(--text-muted)' }}>ID: CHUNK-0{idx + 1}</span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Graph Relationships Triples */}
      {graphContext && graphContext.length > 0 && (
        <div>
          <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--cyan-primary)', textTransform: 'uppercase', marginBottom: '10px' }}>
            GRAPH TRIPLES ({graphContext.length})
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {graphContext.map((rel, idx) => (
              <div 
                key={idx} 
                style={{
                  background: 'var(--bg-surface)',
                  border: '1px solid var(--border-base)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '9px 12px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  color: 'var(--cyan-primary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                <GitCommit size={13} style={{ flexShrink: 0 }} />
                <span>{rel}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Audit Note */}
      <div style={{ marginTop: 'auto', paddingTop: '20px', borderTop: '1px solid var(--border-subtle)', fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.6' }}>
        <p>
          <strong style={{ color: 'var(--text-secondary)' }}>Auditability Guarantee:</strong> All facts are cross-referenced across FAISS semantic embeddings and Neo4j directional paths to ensure strict industrial compliance.
        </p>
      </div>
    </aside>
  );
};
