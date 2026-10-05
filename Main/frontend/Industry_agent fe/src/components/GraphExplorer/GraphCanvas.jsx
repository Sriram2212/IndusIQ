import React, { useState, useEffect, useRef, useMemo } from 'react';
import { 
  Network, 
  Database, 
  ZoomIn, 
  ZoomOut, 
  RefreshCw, 
  Search, 
  Filter, 
  Sparkles, 
  Maximize2, 
  AlertTriangle,
  FileText,
  ShieldCheck,
  Lock,
  MessageSquare,
  Copy,
  Check,
  ChevronRight,
  ExternalLink,
  Flame,
  Activity,
  Layers
} from 'lucide-react';
import { apiClient } from '../../api/client';

export const GraphCanvas = ({ userRole = 'engineer', documents = [], onInvestigateIssue }) => {
  const [rawData, setRawData] = useState({ nodes: [], edges: [] });
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [filterType, setFilterType] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [isLive, setIsLive] = useState(false);
  const [viewMode, setViewMode] = useState('ALL'); // 'ALL' or 'EGO'
  const [activeAsset, setActiveAsset] = useState('');
  const [selectedDoc, setSelectedDoc] = useState('');
  const [docList, setDocList] = useState([]);
  const [copied, setCopied] = useState(false);
  const [showIssuesOnly, setShowIssuesOnly] = useState(false);

  // Pan & Zoom state
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [draggedNode, setDraggedNode] = useState(null);

  const svgRef = useRef(null);

  // Normalize role
  const role = (userRole || 'engineer').toLowerCase();
  const isEngineer = role === 'engineer' || role === 'admin';
  const isTechnician = role === 'technician';
  const isOperator = role === 'operator';

  // Load document list
  useEffect(() => {
    if (documents && documents.length > 0) {
      setDocList(documents);
      if (!selectedDoc && documents.length > 0) {
        setSelectedDoc(documents[0].filename || documents[0].name || '');
      }
    } else {
      apiClient.getDocuments().then(docs => {
        if (Array.isArray(docs)) {
          setDocList(docs);
          if (docs.length > 0 && !selectedDoc) {
            setSelectedDoc(docs[0].filename || docs[0].name || '');
          }
        }
      }).catch(() => {});
    }
  }, [documents]);

  useEffect(() => {
    fetchGraph();
  }, [viewMode, activeAsset, selectedDoc, userRole]);

  const fetchGraph = async () => {
    setLoading(true);
    try {
      const entityParam = viewMode === 'EGO' ? activeAsset : null;
      const docParam = selectedDoc || null;
      const data = await apiClient.getGraphData(entityParam, 120, docParam);
      if (data && Array.isArray(data.nodes)) {
        setIsLive(true);
        setRawData(data);
        if (data.nodes.length > 0) {
          runForceLayout(data.nodes, data.edges || []);
        } else {
          setNodes([]);
          setEdges([]);
          setSelectedNode(null);
        }
      } else {
        setIsLive(false);
        setRawData({ nodes: [], edges: [] });
        setNodes([]);
        setEdges([]);
        setSelectedNode(null);
      }
    } catch (err) {
      console.warn("Error loading graph data:", err);
      setIsLive(false);
      setRawData({ nodes: [], edges: [] });
      setNodes([]);
      setEdges([]);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Physics-based Force Simulation Layout
   * Strong repulsion and collision spacing so nodes never overlap or clump.
   */
  const runForceLayout = (inputNodes, inputEdges) => {
    const width = 1000;
    const height = 650;
    const centerX = width / 2;
    const centerY = height / 2;

    let simNodes = inputNodes.map((n, i) => {
      const angle = (i / Math.max(1, inputNodes.length)) * 2 * Math.PI;
      const dist = 190 + (i % 5) * 65;
      return {
        ...n,
        x: centerX + Math.cos(angle) * dist + (Math.random() - 0.5) * 50,
        y: centerY + Math.sin(angle) * dist + (Math.random() - 0.5) * 50,
        vx: 0,
        vy: 0
      };
    });

    const iterations = 80;
    const repulsion = 9200;
    const springLength = 135;
    const springK = 0.045;
    const minDistance = 75; // strict collision radius

    for (let iter = 0; iter < iterations; iter++) {
      // 1. Repulsion
      for (let i = 0; i < simNodes.length; i++) {
        for (let j = i + 1; j < simNodes.length; j++) {
          const n1 = simNodes[i];
          const n2 = simNodes[j];
          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;

          if (dist < 400) {
            const force = repulsion / (dist * dist);
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            n1.vx -= fx;
            n1.vy -= fy;
            n2.vx += fx;
            n2.vy += fy;
          }

          // Hard collision avoidance
          if (dist < minDistance) {
            const overlap = (minDistance - dist) * 0.5;
            const ox = (dx / dist) * overlap;
            const oy = (dy / dist) * overlap;
            n1.x -= ox;
            n1.y -= oy;
            n2.x += ox;
            n2.y += oy;
          }
        }
      }

      // 2. Spring Attraction for Edges
      for (const edge of inputEdges) {
        const src = simNodes.find(n => n.id === edge.source);
        const tgt = simNodes.find(n => n.id === edge.target);
        if (src && tgt) {
          const dx = tgt.x - src.x;
          const dy = tgt.y - src.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const displacement = dist - springLength;
          const force = displacement * springK;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;

          src.vx += fx;
          src.vy += fy;
          tgt.vx -= fx;
          tgt.vy -= fy;
        }
      }

      // 3. Center Gravity & Boundary
      for (const n of simNodes) {
        n.vx += (centerX - n.x) * 0.018;
        n.vy += (centerY - n.y) * 0.018;

        n.x += n.vx * 0.5;
        n.y += n.vy * 0.5;
        n.vx *= 0.6;
        n.vy *= 0.6;

        n.x = Math.max(75, Math.min(width - 75, n.x));
        n.y = Math.max(65, Math.min(height - 65, n.y));
      }
    }

    setNodes(simNodes);
    setEdges(inputEdges);

    // Pick initial focus
    const primary = simNodes.find(n => (n.type || '').toLowerCase() === 'issue') ||
                    simNodes.find(n => (n.type || '').toLowerCase() === 'equipment') ||
                    simNodes[0];
    setSelectedNode(primary || null);
  };

  const equipmentOptions = useMemo(() => {
    const list = nodes.filter(n => n.type === 'Equipment' || n.type === 'Asset');
    return Array.from(new Set(list.map(n => n.label || n.id)));
  }, [nodes]);

  const issueNodes = useMemo(() => {
    return nodes.filter(n => (n.type || '').toLowerCase() === 'issue' || (n.label || '').toLowerCase().includes('fault') || (n.label || '').toLowerCase().includes('crack') || (n.label || '').toLowerCase().includes('abnormal'));
  }, [nodes]);

  const nodeLabels = useMemo(() => {
    const types = new Set(nodes.map(n => (n.type || 'Entity').toUpperCase()));
    return ['ALL', ...Array.from(types)];
  }, [nodes]);

  // Filtered Nodes
  const visibleNodes = useMemo(() => {
    return nodes.filter(n => {
      if (showIssuesOnly) {
        const isIssue = (n.type || '').toLowerCase() === 'issue' || (n.label || '').toLowerCase().includes('fault') || (n.label || '').toLowerCase().includes('crack');
        // also keep nodes directly connected to issues
        const connectedToIssue = edges.some(e => 
          (e.source === n.id && issueNodes.some(i => i.id === e.target)) ||
          (e.target === n.id && issueNodes.some(i => i.id === e.source))
        );
        return isIssue || connectedToIssue;
      }
      const matchesFilter = filterType === 'ALL' || (n.type || '').toUpperCase() === filterType.toUpperCase();
      const matchesSearch = !searchQuery || (n.label || '').toLowerCase().includes(searchQuery.toLowerCase()) || (n.id || '').toLowerCase().includes(searchQuery.toLowerCase());
      return matchesFilter && matchesSearch;
    });
  }, [nodes, filterType, searchQuery, showIssuesOnly, issueNodes, edges]);

  const visibleNodeIds = useMemo(() => new Set(visibleNodes.map(n => n.id)), [visibleNodes]);

  const visibleEdges = useMemo(() => {
    return edges.filter(e => visibleNodeIds.has(e.source) && visibleNodeIds.has(e.target));
  }, [edges, visibleNodeIds]);

  // Spotlight active connections
  const activeFocusNode = hoveredNode || selectedNode;
  const directNeighborIds = useMemo(() => {
    if (!activeFocusNode) return new Set();
    const set = new Set([activeFocusNode.id]);
    for (const e of visibleEdges) {
      if (e.source === activeFocusNode.id) set.add(e.target);
      if (e.target === activeFocusNode.id) set.add(e.source);
    }
    return set;
  }, [activeFocusNode, visibleEdges]);

  // Color mapper
  const getNodeColor = (type) => {
    switch ((type || '').toLowerCase()) {
      case 'equipment': return 'var(--amber-primary)';
      case 'component': return 'var(--cyan-primary)';
      case 'technician': return 'var(--emerald-primary)';
      case 'issue': return 'var(--rose-primary)';
      case 'process': return 'var(--violet-primary)';
      case 'sensor': return '#e879f9';
      case 'location': return '#38bdf8';
      case 'material': return '#fb923c';
      default: return 'var(--text-secondary)';
    }
  };

  // Pan & Zoom Event Handlers
  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    setZoom(prev => Math.max(0.4, Math.min(2.5, prev * zoomFactor)));
  };

  const handleMouseDown = (e) => {
    if (e.target.tagName === 'svg' || e.target.tagName === 'rect') {
      setIsPanning(true);
      setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e) => {
    if (isPanning) {
      setPan({ x: e.clientX - panStart.x, y: e.clientY - panStart.y });
    } else if (draggedNode) {
      const svg = svgRef.current;
      if (svg) {
        const CTM = svg.getScreenCTM();
        if (CTM) {
          const mouseX = (e.clientX - CTM.e) / CTM.a;
          const mouseY = (e.clientY - CTM.f) / CTM.d;
          const adjustedX = (mouseX - pan.x) / zoom;
          const adjustedY = (mouseY - pan.y) / zoom;

          setNodes(prev => prev.map(n => n.id === draggedNode.id ? { ...n, x: adjustedX, y: adjustedY } : n));
        }
      }
    }
  };

  const handleMouseUp = () => {
    setIsPanning(false);
    setDraggedNode(null);
  };

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const handleCopyIssueContext = (node) => {
    if (!node) return;
    const connectedEdges = edges.filter(e => e.source === node.id || e.target === node.id);
    const relatedNames = connectedEdges.map(e => e.source === node.id ? e.target : e.source).join(', ');
    const text = `[INDUS-IQ GRAPH ISSUE ALERT]\nIssue: ${node.label || node.id}\nOntology Type: ${node.type}\nSource Document: ${node.properties?.source_doc || selectedDoc || 'transformer_inspection_report.pdf'}\nConnected Equipment/Components: ${relatedNames || 'N/A'}\nProperties: ${JSON.stringify(node.properties || {}, null, 2)}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleAskAboutNode = (node) => {
    if (!node) return;
    const prompt = (node.type || '').toLowerCase() === 'issue'
      ? `Investigate issue "${node.label || node.id}" extracted from the inspection report. What is the root cause, severity risk, and required maintenance procedure?`
      : `What is the operational status, inspection history, and connected subsystems for ${node.label || node.id}?`;
    if (onInvestigateIssue) {
      onInvestigateIssue(prompt);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      
      {/* ── Top Header & RBAC Clearance Bar ─────────────────────────────── */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '12px',
        background: 'var(--bg-surface)',
        padding: '12px 16px',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-base)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Network size={20} style={{ color: 'var(--cyan-primary)' }} />
            <h2 style={{ fontSize: '17px', color: '#ffffff', margin: 0, fontWeight: 700 }}>
              Neo4j Knowledge Graph Explorer
            </h2>
          </div>

          {/* RBAC Role Clearance Badge */}
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            background: isEngineer ? 'rgba(245, 158, 11, 0.12)' : (isTechnician ? 'rgba(6, 182, 212, 0.12)' : 'rgba(16, 185, 129, 0.12)'),
            border: `1px solid ${isEngineer ? 'rgba(245, 158, 11, 0.4)' : (isTechnician ? 'rgba(6, 182, 212, 0.4)' : 'rgba(16, 185, 129, 0.4)')}`,
            padding: '3px 9px',
            borderRadius: '100px',
            fontSize: '11px',
            fontFamily: 'var(--font-mono)',
            color: isEngineer ? 'var(--amber-primary)' : (isTechnician ? 'var(--cyan-primary)' : 'var(--emerald-primary)')
          }}>
            <ShieldCheck size={13} />
            <span>
              {isEngineer ? 'CHIEF ENGINEER (ALL GRAPH ACCESS)' : (isTechnician ? 'TECHNICIAN (MAINTENANCE & ISSUES)' : 'OPERATOR (TELEMETRY & ASSETS)')}
            </span>
          </div>

          {/* Live Neo4j status */}
          {isLive ? (
            <span style={{ fontSize: '10.5px', fontFamily: 'var(--font-mono)', background: 'var(--emerald-bg)', color: 'var(--emerald-primary)', padding: '3px 8px', borderRadius: '4px', border: '1px solid rgba(16,185,129,0.3)' }}>
              ● LIVE ({nodes.length} NODES &middot; {edges.length} EDGES)
            </span>
          ) : (
            <span style={{ fontSize: '10.5px', fontFamily: 'var(--font-mono)', background: 'rgba(244, 63, 94, 0.1)', color: 'var(--rose-primary)', padding: '3px 8px', borderRadius: '4px', border: '1px solid rgba(244, 63, 94, 0.3)' }}>
              × NEO4J OFFLINE
            </span>
          )}
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          
          {/* PDF-Based Knowledge Graph Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'var(--bg-core)', padding: '4px 8px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <FileText size={13} style={{ color: 'var(--amber-primary)' }} />
            <select
              value={selectedDoc}
              onChange={(e) => setSelectedDoc(e.target.value)}
              style={{
                background: 'transparent',
                color: '#ffffff',
                border: 'none',
                fontSize: '11.5px',
                fontFamily: 'var(--font-mono)',
                outline: 'none',
                maxWidth: '200px',
                cursor: 'pointer'
              }}
              title="Scope Knowledge Graph to a specific PDF document report"
            >
              <option value="" style={{ background: '#0f172a' }}>All Ingested Reports</option>
              {docList.map(d => {
                const fname = d.filename || d.name || String(d);
                return (
                  <option key={fname} value={fname} style={{ background: '#0f172a' }}>
                    📄 {fname}
                  </option>
                );
              })}
            </select>
          </div>

          {/* Subgraph Switcher */}
          <div style={{ display: 'flex', background: 'var(--bg-core)', padding: '2px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <button
              style={{
                fontSize: '11px',
                padding: '4px 8px',
                borderRadius: '4px',
                color: viewMode === 'EGO' ? '#ffffff' : 'var(--text-muted)',
                background: viewMode === 'EGO' ? 'var(--bg-surface-elevated)' : 'transparent',
                fontWeight: viewMode === 'EGO' ? 600 : 400
              }}
              onClick={() => setViewMode('EGO')}
            >
              Focus Subgraph
            </button>
            <button
              style={{
                fontSize: '11px',
                padding: '4px 8px',
                borderRadius: '4px',
                color: viewMode === 'ALL' ? '#ffffff' : 'var(--text-muted)',
                background: viewMode === 'ALL' ? 'var(--bg-surface-elevated)' : 'transparent',
                fontWeight: viewMode === 'ALL' ? 600 : 400
              }}
              onClick={() => setViewMode('ALL')}
            >
              Full Graph
            </button>
          </div>

          {/* Asset Focus */}
          {viewMode === 'EGO' && equipmentOptions.length > 0 && (
            <select
              value={activeAsset}
              onChange={(e) => setActiveAsset(e.target.value)}
              style={{
                background: 'var(--bg-core)',
                color: 'var(--amber-primary)',
                border: '1px solid var(--border-base)',
                borderRadius: 'var(--radius-sm)',
                padding: '5px 8px',
                fontSize: '11.5px',
                fontFamily: 'var(--font-mono)'
              }}
            >
              <option value="" style={{ background: '#0f172a' }}>-- All Equipment --</option>
              {equipmentOptions.map(opt => (
                <option key={opt} value={opt} style={{ background: '#0f172a' }}>{opt}</option>
              ))}
            </select>
          )}

          {/* Search */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'var(--bg-core)', padding: '5px 8px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
            <Search size={12} style={{ color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Search node..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ background: 'transparent', color: '#ffffff', fontSize: '11.5px', width: '100px', border: 'none', outline: 'none' }}
            />
          </div>

          {/* Fast Issues Only Button */}
          {issueNodes.length > 0 && (
            <button
              onClick={() => setShowIssuesOnly(!showIssuesOnly)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                padding: '5px 10px',
                borderRadius: 'var(--radius-sm)',
                fontSize: '11px',
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
                background: showIssuesOnly ? 'var(--rose-primary)' : 'rgba(244, 63, 94, 0.15)',
                color: showIssuesOnly ? '#ffffff' : 'var(--rose-primary)',
                border: '1px solid rgba(244, 63, 94, 0.5)',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
              title="Isolate all reported issues and faults for immediate communication"
            >
              <AlertTriangle size={12} />
              <span>{showIssuesOnly ? 'Show All Nodes' : `⚠ ${issueNodes.length} Issues Detected`}</span>
            </button>
          )}

          <button 
            className="query-submit-btn" 
            style={{ padding: '6px 10px', fontSize: '11px' }}
            onClick={fetchGraph}
            disabled={loading}
            title="Re-run dynamic layout & sync database"
          >
            <RefreshCw size={11} className={loading ? 'animate-spin' : ''} />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {/* ── Type Filter Chips ───────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', textTransform: 'uppercase', marginRight: '4px' }}>
          ONTOLOGY FILTERS:
        </span>
        {nodeLabels.map(t => (
          <button
            key={t}
            className="preset-chip-btn"
            style={{
              borderColor: filterType === t ? 'var(--cyan-primary)' : 'var(--border-subtle)',
              color: filterType === t ? '#ffffff' : 'var(--text-secondary)',
              background: filterType === t ? 'var(--cyan-bg)' : 'var(--bg-surface)',
              fontSize: '11px',
              padding: '3px 9px'
            }}
            onClick={() => {
              setShowIssuesOnly(false);
              setFilterType(t);
            }}
          >
            {t}
          </button>
        ))}
      </div>

      {/* ── Main Canvas & Detail Drawer Grid ────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '16px' }}>
        
        {/* SVG Graph Canvas Container */}
        <div 
          className="graph-canvas-container" 
          style={{ position: 'relative', height: '640px', cursor: isPanning ? 'grabbing' : 'grab' }}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          {/* Zoom / Pan Controls Overlay */}
          <div style={{ position: 'absolute', top: '14px', right: '14px', display: 'flex', flexDirection: 'column', gap: '6px', zIndex: 10 }}>
            <button 
              onClick={() => setZoom(prev => Math.min(2.5, prev + 0.15))}
              style={{ background: 'var(--bg-surface-elevated)', border: '1px solid var(--border-base)', color: '#ffffff', padding: '6px', borderRadius: '4px', cursor: 'pointer' }}
              title="Zoom In"
            >
              <ZoomIn size={14} />
            </button>
            <button 
              onClick={() => setZoom(prev => Math.max(0.4, prev - 0.15))}
              style={{ background: 'var(--bg-surface-elevated)', border: '1px solid var(--border-base)', color: '#ffffff', padding: '6px', borderRadius: '4px', cursor: 'pointer' }}
              title="Zoom Out"
            >
              <ZoomOut size={14} />
            </button>
            <button 
              onClick={resetView}
              style={{ background: 'var(--bg-surface-elevated)', border: '1px solid var(--border-base)', color: '#ffffff', padding: '6px', borderRadius: '4px', cursor: 'pointer' }}
              title="Reset View"
            >
              <Maximize2 size={14} />
            </button>
          </div>

          {loading ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', gap: '12px' }}>
              <RefreshCw size={28} className="animate-spin" style={{ color: 'var(--cyan-primary)' }} />
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px' }}>Resolving Knowledge Graph &amp; Force Simulation...</span>
            </div>
          ) : nodes.length === 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: '32px', textAlign: 'center' }}>
              <div style={{ width: '56px', height: '56px', borderRadius: '50%', background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                <Database size={28} style={{ color: 'var(--rose-primary)' }} />
              </div>
              <h3 style={{ fontSize: '16px', color: '#ffffff', marginBottom: '6px' }}>
                No Knowledge Graph Entities For This Filter
              </h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', maxWidth: '460px', marginBottom: '16px', lineHeight: '1.5' }}>
                Upload or select a PDF inspection document in the Vault to extract ontology nodes into Neo4j.
              </p>
              <button 
                onClick={fetchGraph}
                className="query-submit-btn" 
                style={{ padding: '8px 18px', fontSize: '12px' }}
              >
                <RefreshCw size={13} />
                <span>Reload Graph</span>
              </button>
            </div>
          ) : (
            <svg 
              ref={svgRef}
              width="100%" 
              height="100%" 
              viewBox="0 0 1000 650" 
              style={{ background: 'var(--bg-core)' }}
            >
              <defs>
                <marker id="arrow" viewBox="0 -5 10 10" refX="24" refY="0" markerWidth="6" markerHeight="6" orient="auto">
                  <path d="M0,-4L8,0L0,4" fill="var(--steel-500)" />
                </marker>
                <marker id="arrow-active" viewBox="0 -5 10 10" refX="24" refY="0" markerWidth="7" markerHeight="7" orient="auto">
                  <path d="M0,-4L8,0L0,4" fill="var(--amber-primary)" />
                </marker>
                <marker id="arrow-issue" viewBox="0 -5 10 10" refX="24" refY="0" markerWidth="7" markerHeight="7" orient="auto">
                  <path d="M0,-4L8,0L0,4" fill="var(--rose-primary)" />
                </marker>
              </defs>

              {/* Viewport Transform Group for Zoom and Pan */}
              <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
                
                {/* 1. Draw Edges */}
                {visibleEdges.map((edge, idx) => {
                  const srcNode = nodes.find(n => n.id === edge.source);
                  const tgtNode = nodes.find(n => n.id === edge.target);
                  if (!srcNode || !tgtNode) return null;

                  const isEdgeActive = activeFocusNode && (activeFocusNode.id === srcNode.id || activeFocusNode.id === tgtNode.id);
                  const isIssueEdge = edge.label === 'HAS_ISSUE' || edge.label === 'HAS_FAULT' || (srcNode.type === 'Issue' || tgtNode.type === 'Issue');
                  const isDimmed = activeFocusNode && !isEdgeActive;

                  return (
                    <g key={idx} opacity={isDimmed ? 0.08 : (isEdgeActive ? 1 : 0.5)}>
                      <line
                        x1={srcNode.x}
                        y1={srcNode.y}
                        x2={tgtNode.x}
                        y2={tgtNode.y}
                        stroke={isIssueEdge ? 'var(--rose-primary)' : (isEdgeActive ? 'var(--amber-primary)' : 'var(--steel-600)')}
                        strokeWidth={isIssueEdge ? '2.5' : (isEdgeActive ? '2.5' : '1.3')}
                        markerEnd={isIssueEdge ? "url(#arrow-issue)" : (isEdgeActive ? "url(#arrow-active)" : "url(#arrow)")}
                        strokeDasharray={isIssueEdge ? '5 3' : (edge.label === 'MONITORS' ? '4 4' : 'none')}
                      />

                      {/* Edge Label Pill */}
                      {isEdgeActive && (
                        <g transform={`translate(${(srcNode.x + tgtNode.x) / 2}, ${(srcNode.y + tgtNode.y) / 2})`}>
                          <rect
                            x="-34"
                            y="-9"
                            width="68"
                            height="16"
                            rx="3"
                            fill="var(--bg-core)"
                            stroke={isIssueEdge ? 'var(--rose-primary)' : 'var(--amber-dim)'}
                            strokeWidth="1"
                          />
                          <text
                            textAnchor="middle"
                            dy="3"
                            fill={isIssueEdge ? 'var(--rose-primary)' : 'var(--amber-primary)'}
                            fontSize="8.5px"
                            fontFamily="var(--font-mono)"
                            fontWeight="600"
                          >
                            {edge.label}
                          </text>
                        </g>
                      )}
                    </g>
                  );
                })}

                {/* 2. Draw Nodes */}
                {visibleNodes.map((node) => {
                  const isSelected = selectedNode && selectedNode.id === node.id;
                  const isHovered = hoveredNode && hoveredNode.id === node.id;
                  const isConnected = directNeighborIds.has(node.id);
                  const isDimmed = activeFocusNode && !isConnected;
                  const isIssueNode = (node.type || '').toLowerCase() === 'issue' || (node.label || '').toLowerCase().includes('crack') || (node.label || '').toLowerCase().includes('fault');
                  const color = getNodeColor(node.type);

                  const isMajorEquipment = (node.type || '').toLowerCase() === 'equipment';
                  const radius = isSelected ? 24 : (isMajorEquipment ? 20 : (isIssueNode ? 18 : 15));

                  return (
                    <g
                      key={node.id}
                      transform={`translate(${node.x}, ${node.y})`}
                      style={{ cursor: 'pointer' }}
                      opacity={isDimmed ? 0.16 : 1}
                      onClick={() => setSelectedNode(node)}
                      onMouseEnter={() => setHoveredNode(node)}
                      onMouseLeave={() => setHoveredNode(null)}
                      onMouseDown={(e) => {
                        e.stopPropagation();
                        setDraggedNode(node);
                      }}
                    >
                      {/* Issue Pulsing Hazard Halo */}
                      {isIssueNode && (
                        <circle
                          r={radius + 10}
                          fill="none"
                          stroke="var(--rose-primary)"
                          strokeWidth="2"
                          opacity="0.6"
                          strokeDasharray="4 2"
                          style={{ filter: 'drop-shadow(0 0 10px rgba(244,63,94,0.8))' }}
                        />
                      )}

                      {/* Halo Glow for Selected/Hovered Node */}
                      {(isSelected || isHovered) && (
                        <circle
                          r={radius + 8}
                          fill="none"
                          stroke={color}
                          strokeWidth="2"
                          opacity="0.5"
                          style={{ filter: `drop-shadow(0 0 10px ${color})` }}
                        />
                      )}

                      {/* Main Node Circle */}
                      <circle
                        r={radius}
                        fill="var(--bg-surface-elevated)"
                        stroke={isIssueNode ? 'var(--rose-primary)' : color}
                        strokeWidth={isSelected ? '3' : (isIssueNode ? '2.5' : '2')}
                        style={{
                          filter: isSelected ? `drop-shadow(0 0 14px ${color})` : (isIssueNode ? 'drop-shadow(0 0 8px rgba(244,63,94,0.6))' : 'none'),
                          transition: 'stroke-width 0.15s ease'
                        }}
                      />

                      {/* Node Initial Indicator */}
                      <text
                        textAnchor="middle"
                        dy="4.5"
                        fill={isIssueNode ? 'var(--rose-primary)' : color}
                        fontFamily="var(--font-display)"
                        fontWeight="800"
                        fontSize={isMajorEquipment ? '13px' : '11px'}
                      >
                        {isIssueNode ? '⚠' : (node.type || 'E')[0]}
                      </text>

                      {/* Node Text Label with Contrast Pill */}
                      <g transform={`translate(0, ${radius + 14})`}>
                        <rect
                          x={-((node.label?.length || 10) * 3.5) - 6}
                          y="-9"
                          width={(node.label?.length || 10) * 7 + 12}
                          height="17"
                          rx="4"
                          fill="rgba(9, 12, 16, 0.9)"
                          stroke={isSelected ? color : (isIssueNode ? 'rgba(244,63,94,0.5)' : 'var(--border-subtle)')}
                          strokeWidth={isSelected ? '1.5' : '0.8'}
                        />
                        <text
                          textAnchor="middle"
                          dy="3.5"
                          fill={isSelected ? '#ffffff' : (isIssueNode ? 'var(--rose-primary)' : 'var(--text-primary)')}
                          fontSize="10px"
                          fontWeight={isSelected || isIssueNode ? '700' : '500'}
                          fontFamily="var(--font-sans)"
                        >
                          {node.label}
                        </text>
                      </g>
                    </g>
                  );
                })}
              </g>
            </svg>
          )}

          {/* Bottom Canvas Stats Pill */}
          <div style={{ position: 'absolute', bottom: '14px', left: '14px', display: 'flex', gap: '8px', pointerEvents: 'none' }}>
            <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', background: 'var(--bg-glass-heavy)', padding: '5px 10px', borderRadius: '4px', border: '1px solid var(--border-base)', color: 'var(--text-secondary)' }}>
              REPORT: {selectedDoc || 'All Documents'} &middot; VISIBLE: {visibleNodes.length} NODES &middot; ZOOM: {Math.round(zoom * 100)}%
            </span>
          </div>
        </div>

        {/* ── Node Detail & Communication Inspector Drawer ─────────────── */}
        <div className="card-widget" style={{ display: 'flex', flexDirection: 'column', gap: '14px', overflowY: 'auto', maxHeight: '640px' }}>
          
          <div style={{ paddingBottom: '10px', borderBottom: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', color: getNodeColor(selectedNode?.type || ''), letterSpacing: '0.08em', fontWeight: 700 }}>
                {selectedNode?.type || 'Entity'} Inspector
              </span>
              {selectedNode && (
                <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  RBAC: {userRole.toUpperCase()}
                </span>
              )}
            </div>
            <h3 style={{ fontSize: '15px', color: '#ffffff', marginTop: '4px', wordBreak: 'break-word', lineHeight: '1.3' }}>
              {selectedNode?.label || 'Click a node to inspect'}
            </h3>
          </div>

          {selectedNode ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              
              {/* Quick Communication / Investigation Actions */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <button
                  type="button"
                  onClick={() => handleAskAboutNode(selectedNode)}
                  className="query-submit-btn"
                  style={{
                    width: '100%',
                    justifyContent: 'center',
                    padding: '8px 12px',
                    fontSize: '12px',
                    background: (selectedNode.type || '').toLowerCase() === 'issue' ? 'var(--rose-primary)' : 'var(--amber-primary)'
                  }}
                  title="Ask Copilot natural language questions about this specific entity"
                >
                  <MessageSquare size={13} />
                  <span>{(selectedNode.type || '').toLowerCase() === 'issue' ? 'Diagnose Issue with Copilot' : 'Investigate in Copilot'}</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleCopyIssueContext(selectedNode)}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px',
                    padding: '7px 12px',
                    fontSize: '11.5px',
                    fontFamily: 'var(--font-mono)',
                    background: 'var(--bg-surface-elevated)',
                    color: copied ? 'var(--emerald-primary)' : 'var(--text-secondary)',
                    border: '1px solid var(--border-base)',
                    borderRadius: 'var(--radius-sm)',
                    cursor: 'pointer'
                  }}
                  title="Copy entity details for team communication"
                >
                  {copied ? <Check size={12} /> : <Copy size={12} />}
                  <span>{copied ? 'Copied to Clipboard!' : 'Copy Context for Team'}</span>
                </button>
              </div>

              {/* Source Document Provenance */}
              <div style={{ background: 'var(--bg-core)', padding: '8px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>SOURCE DOCUMENT PROVENANCE</div>
                <div style={{ fontSize: '12px', color: 'var(--amber-primary)', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <FileText size={12} />
                  <span>{selectedNode.properties?.source_doc || selectedDoc || 'transformer_inspection_report.pdf'}</span>
                </div>
              </div>

              <div>
                <div style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>CANONICAL IDENTIFIER</div>
                <div style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: 'var(--cyan-primary)', marginTop: '2px', wordBreak: 'break-all' }}>
                  {selectedNode.id}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>ONTOLOGY TYPE</div>
                <div style={{ fontSize: '12.5px', color: getNodeColor(selectedNode.type), marginTop: '2px', fontWeight: 700 }}>
                  {selectedNode.type || 'Entity'}
                </div>
              </div>

              {/* Real Neo4j Properties */}
              {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                <div>
                  <div style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '6px' }}>
                    NEO4J PROPERTIES
                  </div>
                  <div style={{ background: 'var(--bg-core)', borderRadius: 'var(--radius-sm)', padding: '8px 10px', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {Object.entries(selectedNode.properties).map(([k, v]) => (
                      <div key={k} style={{ fontSize: '11px', display: 'flex', justifyContent: 'space-between', gap: '8px' }}>
                        <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{k}:</span>
                        <span style={{ color: 'var(--text-primary)', textAlign: 'right', wordBreak: 'break-word' }}>{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Connected Relationships in Neo4j */}
              <div style={{ paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '8px' }}>
                  CONNECTED EDGES ({edges.filter(e => e.source === selectedNode.id || e.target === selectedNode.id).length})
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                  {edges
                    .filter(e => e.source === selectedNode.id || e.target === selectedNode.id)
                    .map((e, idx) => {
                      const isSource = e.source === selectedNode.id;
                      const neighborId = isSource ? e.target : e.source;
                      const neighbor = nodes.find(n => n.id === neighborId);

                      return (
                        <div 
                          key={idx} 
                          style={{ fontSize: '11px', color: 'var(--text-secondary)', background: 'var(--bg-surface-elevated)', padding: '6px 8px', borderRadius: '4px', cursor: 'pointer', border: '1px solid var(--border-subtle)' }}
                          onClick={() => neighbor && setSelectedNode(neighbor)}
                          title="Click to focus neighbor node"
                        >
                          <span style={{ color: 'var(--amber-primary)', fontFamily: 'var(--font-mono)', fontSize: '9.5px' }}>
                            {isSource ? `—[${e.label}]→` : `←[${e.label}]—`}
                          </span>{' '}
                          <span style={{ color: '#ffffff' }}>{neighbor?.label || neighborId}</span>
                        </div>
                      );
                    })}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
              Click any node in the Knowledge Graph canvas to inspect its Neo4j properties, relationships, and issue details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
