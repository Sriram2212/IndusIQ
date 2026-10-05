import React, { useState, useEffect, useRef } from 'react';
import { 
  MessageSquare, 
  Network, 
  FolderArchive, 
  Activity, 
  GitFork, 
  Plus,
  Trash2,
  Circle,
  ArrowRight
} from 'lucide-react';
import { apiClient } from '../api/client';

/* ─── Mini Knowledge Graph Preview ─── */
const MOCK_MINI_NODES = [
  { id: 'Pump-A1', x: 60,  y: 55,  type: 'Equipment', color: '#f59e0b' },
  { id: 'Motor-B2', x: 140, y: 30,  type: 'Equipment', color: '#f59e0b' },
  { id: 'Valve-C3', x: 200, y: 80,  type: 'Component', color: '#06b6d4' },
  { id: 'Bearing', x: 100, y: 95,  type: 'Component', color: '#06b6d4' },
  { id: 'Sensor-01', x: 190, y: 40,  type: 'Sensor',    color: '#10b981' },
  { id: 'Fault-Log', x: 50,  y: 100, type: 'Issue',     color: '#f43f5e' },
  { id: 'Unit-2',   x: 250, y: 60,  type: 'Location',   color: '#8b5cf6' },
];
const MOCK_MINI_EDGES = [
  ['Pump-A1', 'Bearing'],
  ['Pump-A1', 'Motor-B2'],
  ['Motor-B2', 'Sensor-01'],
  ['Valve-C3', 'Unit-2'],
  ['Pump-A1', 'Fault-Log'],
  ['Bearing', 'Valve-C3'],
];

function MiniGraphPreview({ onNavigateToGraph }) {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [isLive, setIsLive] = useState(false);
  const [nodeCount, setNodeCount] = useState(0);
  const [edgeCount, setEdgeCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await apiClient.getGraphData(null, 12);
        if (!cancelled && data && data.nodes && data.nodes.length > 0) {
          // Layout top 8 nodes in a compact area (270 x 120)
          const width = 270, height = 120;
          const n = data.nodes.slice(0, 8).map((node, i) => {
            const angle = (i / Math.max(1, Math.min(data.nodes.length, 8))) * 2 * Math.PI;
            const r = 40 + (i % 2) * 20;
            return {
              id: node.id,
              x: width / 2 + Math.cos(angle) * r,
              y: height / 2 + Math.sin(angle) * r * 0.6,
              type: node.type,
              color: getNodeColor(node.type),
            };
          });
          const ids = new Set(n.map(x => x.id));
          const e = data.edges.filter(ed => ids.has(ed.source) && ids.has(ed.target)).slice(0, 10);
          setNodes(n);
          setEdges(e);
          setNodeCount(data.count?.nodes || data.nodes.length);
          setEdgeCount(data.count?.edges || data.edges.length);
          setIsLive(true);
        } else if (!cancelled) {
          setNodes([]);
          setEdges([]);
          setNodeCount(0);
          setEdgeCount(0);
          setIsLive(true);
        }
      } catch {
        if (!cancelled) {
          setNodes([]);
          setEdges([]);
          setNodeCount(0);
          setEdgeCount(0);
          setIsLive(false);
        }
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const nodeMap = Object.fromEntries(nodes.map(n => [n.id, n]));

  return (
    <div className="mini-graph-preview-card" onClick={onNavigateToGraph} title="Open Knowledge Graph Explorer">
      <div className="mini-graph-header">
        <span className="mini-graph-title">Knowledge Graph</span>
        <span className={`mini-graph-badge ${isLive ? 'live' : 'demo'}`}>
          {isLive ? '● LIVE' : '◎ DEMO'}
        </span>
      </div>

      <div className="mini-graph-svg-container">
        <svg viewBox="0 0 270 120" preserveAspectRatio="xMidYMid meet">
          <defs>
            <radialGradient id="mgGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="rgba(6,182,212,0.1)" />
              <stop offset="100%" stopColor="transparent" />
            </radialGradient>
          </defs>
          {/* Background subtle glow */}
          <ellipse cx="135" cy="60" rx="100" ry="50" fill="url(#mgGlow)" />

          {/* Edges */}
          {edges.map((edge, i) => {
            const src = nodeMap[edge.source];
            const tgt = nodeMap[edge.target];
            if (!src || !tgt) return null;
            return (
              <line
                key={i}
                x1={src.x} y1={src.y}
                x2={tgt.x} y2={tgt.y}
                stroke="rgba(255,255,255,0.12)"
                strokeWidth="1"
              />
            );
          })}

          {/* Nodes */}
          {nodes.map((node) => (
            <g key={node.id}>
              <circle
                cx={node.x}
                cy={node.y}
                r="5"
                fill={node.color}
                opacity="0.9"
                filter="url(#nodeBlur)"
              />
              <circle
                cx={node.x}
                cy={node.y}
                r="3"
                fill={node.color}
              />
            </g>
          ))}
        </svg>
      </div>

      <div className="mini-graph-footer">
        <span style={{ color: 'var(--cyan-primary)' }}>
          <Network size={10} /> {nodeCount} nodes
        </span>
        <span>
          {edgeCount} edges
        </span>
        <span style={{ color: 'var(--amber-primary)' }}>
          Explore <ArrowRight size={9} />
        </span>
      </div>
    </div>
  );
}

/* ─── Time ago helper ─── */
function timeAgo(isoString) {
  if (!isoString) return '';
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function getNodeColor(type) {
  const map = {
    Equipment: '#f59e0b',
    Component: '#06b6d4',
    Sensor:    '#10b981',
    Issue:     '#f43f5e',
    Location:  '#8b5cf6',
    Process:   '#e879f9',
    Material:  '#a3e635',
  };
  return map[type] || '#64748b';
}

/* ─── Main Sidebar ─── */
export const Sidebar = ({ 
  activeTab, 
  setActiveTab, 
  docCount = 0, 
  selectedAsset, 
  onSelectAsset,
  chatSessions = [],
  currentSessionId = null,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  isSidebarOpen = true,
  assets = [],
  userRole = 'engineer'
}) => {
  const normRole = (userRole || 'engineer').toLowerCase();
  const roleLabel = normRole === 'engineer' || normRole === 'admin' 
    ? 'ENG Clearance' 
    : (normRole === 'technician' ? 'TECH Clearance' : 'OPE Clearance');
  const roleColor = normRole === 'engineer' || normRole === 'admin'
    ? 'var(--amber-primary)'
    : (normRole === 'technician' ? 'var(--cyan-primary)' : 'var(--emerald-primary)');

  return (
    <aside className={`sidebar-nav ${isSidebarOpen ? '' : 'collapsed'}`}>
      <div className="sidebar-scrollable-content">
        {/* Navigation Section */}
        <div className="nav-section-title">Workspace</div>
        <div className="nav-group">
          <button 
            className={`nav-tab-btn ${activeTab === 'query' ? 'active' : ''}`}
            onClick={() => setActiveTab('query')}
          >
            <div className="nav-btn-content">
              <MessageSquare className="nav-icon" />
              <span>Ask &amp; Investigate</span>
            </div>
            <span className="nav-chip">AI Copilot</span>
          </button>

          <button 
            className={`nav-tab-btn ${activeTab === 'graph' ? 'active' : ''}`}
            onClick={() => setActiveTab('graph')}
          >
            <div className="nav-btn-content">
              <Network className="nav-icon" />
              <span>Knowledge Graph</span>
            </div>
            <span className="nav-chip" style={{ color: roleColor }}>{roleLabel}</span>
          </button>

          <button 
            className={`nav-tab-btn ${activeTab === 'vault' ? 'active' : ''}`}
            onClick={() => setActiveTab('vault')}
          >
            <div className="nav-btn-content">
              <FolderArchive className="nav-icon" />
              <span>Document Vault</span>
            </div>
            <span className="nav-chip">{docCount} docs</span>
          </button>

          <button 
            className={`nav-tab-btn ${activeTab === 'telemetry' ? 'active' : ''}`}
            onClick={() => setActiveTab('telemetry')}
          >
            <div className="nav-btn-content">
              <Activity className="nav-icon" />
              <span>System Telemetry</span>
            </div>
            <span className="nav-chip">Live</span>
          </button>
        </div>

        {/* Mini Knowledge Graph Preview */}
        <div className="nav-section-title mini-graph-section">Graph Preview</div>
        <div style={{ padding: '0 0 20px 0' }}>
          <MiniGraphPreview onNavigateToGraph={() => setActiveTab('graph')} />
        </div>

        {/* Chat History Section */}
        <div className="nav-section-title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Chat History</span>
          <button 
            onClick={onNewChat} 
            className="new-chat-btn" 
            title="Start New Chat (N)"
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--amber-primary)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              padding: '2px'
            }}
          >
            <Plus size={14} />
          </button>
        </div>
        <div className="nav-group chat-sessions-list" style={{ maxHeight: '200px', overflowY: 'auto', gap: '3px', marginBottom: '24px' }}>
          {chatSessions.length === 0 ? (
            <div className="empty-history-text" style={{ padding: '10px 10px', fontSize: '11px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
              No past conversations
            </div>
          ) : (
            chatSessions.map((session) => (
              <div 
                key={session.session_id}
                className={`chat-session-item ${currentSessionId === session.session_id ? 'active' : ''}`}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  padding: '8px 10px',
                  borderRadius: 'var(--radius-sm)',
                  cursor: 'pointer',
                  fontSize: '12px',
                  background: currentSessionId === session.session_id ? 'var(--bg-surface-elevated)' : 'transparent',
                  border: currentSessionId === session.session_id ? '1px solid var(--border-base)' : '1px solid transparent',
                  color: currentSessionId === session.session_id ? '#ffffff' : 'var(--text-secondary)',
                  transition: 'all 0.2s'
                }}
                onClick={() => onSelectSession && onSelectSession(session.session_id)}
              >
                {/* Row 1: title + delete */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '6px' }}>
                  <div style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', flex: 1 }}>
                    {session.title || 'Untitled Conversation'}
                  </div>
                  <button
                    className="delete-session-btn"
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-muted)',
                      cursor: 'pointer',
                      opacity: 0,
                      padding: '2px',
                      transition: 'opacity 0.2s',
                      flexShrink: 0
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onDeleteSession) onDeleteSession(session.session_id);
                    }}
                  >
                    <Trash2 size={11} className="trash-icon" />
                  </button>
                </div>
                {/* Row 2: message count + time */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
                  {session.message_count !== undefined && (
                    <span className="session-msg-count">{session.message_count} msgs</span>
                  )}
                  <span className="session-time-ago">{timeAgo(session.last_updated)}</span>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Plant Asset Hierarchy */}
        <div className="nav-section-title">Discovered Plant Assets ({assets.length})</div>
        <div className="nav-group" style={{ gap: '2px', marginBottom: '16px' }}>
          {assets.length === 0 ? (
            <div style={{ padding: '8px 12px', fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
              No assets discovered. Upload operational documents in Vault to extract equipment.
            </div>
          ) : (
            assets.map(asset => {
              const assetName = asset.name || asset.id;
              const isSelected = selectedAsset === assetName;
              const isAlert = asset.status === 'Critical' || asset.status === 'Warning';
              return (
                <div 
                  key={asset.id || assetName}
                  className={`plant-asset-item ${isSelected ? 'active' : ''}`}
                  onClick={() => onSelectAsset && onSelectAsset(assetName)}
                  style={{ fontWeight: isSelected ? 600 : 400 }}
                >
                  <span className={`asset-dot ${isAlert ? 'amber' : 'green'}`} />
                  <span>{assetName} {asset.type && asset.type !== 'Equipment' ? `(${asset.type})` : ''}</span>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Footer / Engine Info */}
      <div className="sidebar-footer">
        <div className="langgraph-badge-card">
          <div className="langgraph-icon">
            <GitFork size={15} />
          </div>
          <div className="langgraph-text">
            <h5 style={{ color: '#ffffff' }}>LangGraph 1.2 Engine</h5>
            <p>Self-Corrective Multi-Agent RAG</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
