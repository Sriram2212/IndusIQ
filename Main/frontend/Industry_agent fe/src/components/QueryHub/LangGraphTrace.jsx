import React, { useState, useEffect } from 'react';
import { GitFork, CheckCircle2, Loader2, ChevronDown, ChevronUp } from 'lucide-react';

const GRAPH_NODES = [
  { id: 'extract',      name: 'Extract & Decompose',       desc: 'LLM + Regex Fallback' },
  { id: 'canonicalize', name: 'Canonicalize Entities',     desc: 'Dynamic Synonym Resolver' },
  { id: 'retrieve',     name: 'Hybrid Retrieve',           desc: 'Vector Rerank + Graph BFS' },
  { id: 'validate',     name: 'Validate Evidence',         desc: 'Factuality & Cross-check' },
  { id: 'answer',       name: 'Generate Cited Answer',     desc: 'Role-Grounded Synthesis' },
  { id: 'verify',       name: 'Verify & Calibrate',        desc: 'Confidence & Source Rank' }
];

export const LangGraphTrace = ({ loading = false, hasResponse = false }) => {
  const [activeNodeIndex, setActiveNodeIndex] = useState(0);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    let interval;
    if (loading) {
      setIsExpanded(true);
      setActiveNodeIndex(0);
      interval = setInterval(() => {
        setActiveNodeIndex(prev => (prev < GRAPH_NODES.length - 1 ? prev + 1 : prev));
      }, 700);
    } else {
      setActiveNodeIndex(GRAPH_NODES.length);
    }
    return () => clearInterval(interval);
  }, [loading]);

  if (!loading && !hasResponse) {
    return null;
  }

  // Completed compact pill state when not loading
  if (!loading && hasResponse && !isExpanded) {
    return (
      <div 
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(16, 185, 129, 0.08)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: '6px',
          padding: '6px 14px',
          margin: '0 0 10px 0',
          cursor: 'pointer',
          fontSize: '11.5px',
          fontFamily: 'var(--font-mono)'
        }}
        onClick={() => setIsExpanded(true)}
        title='Click to inspect LangGraph orchestration trace'
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle2 size={13} style={{ color: 'var(--emerald-primary)' }} />
          <span style={{ color: 'var(--emerald-primary)', fontWeight: 600 }}>
            LANGGRAPH ORCHESTRATION PIPELINE EXECUTED (6 NODES COMPLETE)
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-muted)' }}>
          <span>View Steps</span>
          <ChevronDown size={12} />
        </div>
      </div>
    );
  }

  return (
    <div className='langgraph-trace-container animate-fade-in' style={{ marginBottom: '10px' }}>
      <div className='langgraph-header' style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div className='langgraph-title-group'>
          <GitFork className='langgraph-icon' size={14} />
          <span className='langgraph-title'>LangGraph Dynamic Orchestration Graph</span>
          <span className='langgraph-badge'>
            {loading ? 'ACTIVE EXECUTION' : 'COMPLETE'}
          </span>
        </div>
        {!loading && (
          <button
            type='button'
            onClick={() => setIsExpanded(false)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '11px',
              fontFamily: 'var(--font-mono)'
            }}
          >
            <span>Collapse</span>
            <ChevronUp size={12} />
          </button>
        )}
      </div>

      <div className='langgraph-stepper-grid'>
        {GRAPH_NODES.map((node, index) => {
          let status = 'pending';
          if (loading) {
            if (index < activeNodeIndex) status = 'completed';
            else if (index === activeNodeIndex) status = 'active';
            else status = 'pending';
          } else {
            status = 'completed';
          }

          return (
            <div key={node.id} className={langgraph-step-node }>
              <div className='step-node-header'>
                <div className='step-node-number'>0{index + 1}</div>
                <div className='step-node-status-icon'>
                  {status === 'active' && <Loader2 size={12} className='animate-spin' />}
                  {status === 'completed' && <CheckCircle2 size={12} />}
                  {status === 'pending' && <span className='pending-dot' />}
                </div>
              </div>
              <div className='step-node-name'>{node.name}</div>
              <div className='step-node-desc'>{node.desc}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
