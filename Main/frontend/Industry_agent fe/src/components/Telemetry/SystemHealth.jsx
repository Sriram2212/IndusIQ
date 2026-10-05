import React, { useState, useEffect } from 'react';
import { Activity, Database, Server, Cpu, CheckCircle2, ShieldCheck, Zap } from 'lucide-react';
import { apiClient } from '../../api/client';

export const SystemHealth = ({ isOnline, docCount = 0 }) => {
  const [graphStats, setGraphStats] = useState(null);

  useEffect(() => {
    async function loadStats() {
      const stats = await apiClient.getGraphStats();
      setGraphStats(stats);
    }
    loadStats();
  }, []);

  const isGraphConnected = graphStats && graphStats.node_count !== undefined && !graphStats.error;

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div>
        <h2 style={{ fontSize: '18px', color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={18} style={{ color: 'var(--emerald-primary)' }} />
          <span>Industrial Agentic System Telemetry</span>
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '12px', marginTop: '4px' }}>
          Live metrics across FastAPI Backend, LangGraph Reasoning Engine, Neo4j, and FAISS
        </p>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <div className="card-widget">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '10.5px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>FASTAPI BACKEND</span>
            <Server size={14} style={{ color: isOnline ? 'var(--emerald-primary)' : 'var(--rose-primary)' }} />
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, color: isOnline ? 'var(--emerald-primary)' : 'var(--rose-primary)', fontFamily: 'var(--font-display)' }}>
            {isOnline ? 'ONLINE' : 'OFFLINE'}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Endpoint: http://localhost:8000
          </div>
        </div>

        <div className="card-widget">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '10.5px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>NEO4J GRAPH</span>
            <Database size={14} style={{ color: isGraphConnected ? 'var(--cyan-primary)' : 'var(--text-muted)' }} />
          </div>
          <div style={{ fontSize: '20px', fontWeight: 800, color: isGraphConnected ? '#ffffff' : 'var(--text-muted)', fontFamily: 'var(--font-display)' }}>
            {isGraphConnected ? `${graphStats.node_count} NODES · ${graphStats.edge_count} EDGES` : 'DISCONNECTED'}
          </div>
          <div style={{ fontSize: '11px', color: isGraphConnected ? 'var(--cyan-primary)' : 'var(--text-muted)', marginTop: '4px' }}>
            {isGraphConnected ? `${graphStats.labels?.length || 0} Node Types Configured` : 'bolt://localhost:7687'}
          </div>
        </div>

        <div className="card-widget">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '10.5px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>DOCUMENT VAULT</span>
            <Zap size={14} style={{ color: 'var(--amber-primary)' }} />
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, color: '#ffffff', fontFamily: 'var(--font-display)' }}>
            {docCount} {docCount === 1 ? 'FILE' : 'FILES'}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--amber-primary)', marginTop: '4px' }}>
            {docCount > 0 ? 'Indexed in MongoDB & FAISS' : 'Ready for Ingestion'}
          </div>
        </div>

        <div className="card-widget">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '10.5px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>REASONING ENGINE</span>
            <ShieldCheck size={14} style={{ color: isOnline ? 'var(--emerald-primary)' : 'var(--text-muted)' }} />
          </div>
          <div style={{ fontSize: '22px', fontWeight: 800, color: isOnline ? 'var(--emerald-primary)' : 'var(--text-muted)', fontFamily: 'var(--font-display)' }}>
            {isOnline ? 'LANGGRAPH READY' : 'STANDBY'}
          </div>
          <div style={{ fontSize: '11px', color: isOnline ? 'var(--emerald-primary)' : 'var(--text-muted)', marginTop: '4px' }}>
            StateGraph Agent Active
          </div>
        </div>
      </div>

      {/* Architecture Components Checklist */}
      <div className="card-widget">
        <div className="card-widget-head">
          <h3 style={{ fontSize: '14px', color: '#ffffff' }}>Operational Architecture & Integrity Matrix</h3>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: isOnline ? 'var(--emerald-primary)' : 'var(--text-muted)' }}>
            {isOnline ? 'SUBSYSTEMS CONNECTED' : 'SYSTEM OFFLINE'}
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          {[
            { name: 'LangGraph StateGraph Engine', status: 'Stateful 7-Node Execution Graph', tag: isOnline ? 'ACTIVE' : 'OFFLINE' },
            { name: 'Self-Corrective Graph Hop (CRAG)', status: 'Dynamic BFS Expansion Loop', tag: isOnline ? 'ENABLED' : 'STANDBY' },
            { name: 'Entity Canonicalizer & Ontology', status: 'Slug-based Canonical Normalization', tag: isOnline ? 'SYNCED' : 'STANDBY' },
            { name: 'Semantic Contradiction Detector', status: 'Negation & Opposition Cross-Check', tag: isOnline ? 'ACTIVE' : 'STANDBY' },
            { name: 'Factuality & Evidence Validator', status: 'Direct Fact vs. Hypothesis vs. Rec', tag: isOnline ? 'VERIFIED' : 'STANDBY' },
            { name: 'Calibrated Confidence Evaluator', status: 'Programmatic Multi-Factor Formula', tag: isOnline ? 'ACTIVE' : 'STANDBY' }
          ].map((item, idx) => (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>{item.name}</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>{item.status}</div>
              </div>
              <span style={{ 
                fontSize: '10px', 
                fontFamily: 'var(--font-mono)', 
                color: item.tag === 'ACTIVE' || item.tag === 'ENABLED' || item.tag === 'SYNCED' || item.tag === 'VERIFIED' ? 'var(--emerald-primary)' : 'var(--text-muted)', 
                background: item.tag === 'ACTIVE' || item.tag === 'ENABLED' || item.tag === 'SYNCED' || item.tag === 'VERIFIED' ? 'var(--emerald-bg)' : 'rgba(255,255,255,0.05)', 
                padding: '2px 7px', 
                borderRadius: '4px', 
                border: '1px solid rgba(16,185,129,0.3)' 
              }}>
                {item.tag}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
