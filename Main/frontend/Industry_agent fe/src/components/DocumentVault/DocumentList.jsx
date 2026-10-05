import React, { useState, useEffect } from 'react';
import { 
  FileText, Search, ExternalLink, CheckCircle2, Filter, FolderOpen, 
  Trash2, Download, Eye, HardDrive, Layers, ShieldCheck, RefreshCw,
  AlertTriangle, CheckSquare, Square, FileCheck
} from 'lucide-react';
import { apiClient } from '../../api/client';
import { PdfViewerModal } from './PdfViewerModal';
import { useToast } from '../Toast';

export const DocumentList = ({ documents = [], onRefresh, userRole = 'engineer' }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('ALL');
  const [sortBy, setSortBy] = useState('recent'); // 'recent' | 'name' | 'size'
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [previewDoc, setPreviewDoc] = useState(null);
  const [stats, setStats] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [isBulkDeleting, setIsBulkDeleting] = useState(false);
  const toast = useToast();

  const canDelete = (userRole || '').toLowerCase() === 'engineer';

  // Load storage statistics
  const loadStats = async () => {
    const data = await apiClient.getDocumentStats();
    if (data) setStats(data);
  };

  useEffect(() => {
    loadStats();
  }, [documents]);

  const showNotification = (text, type = 'success') => {
    if (type === 'error') toast.error('Error', text);
    else toast.success('Document Management', text);
  };

  // Filter and Sort Logic
  const filteredDocs = (documents || []).filter(doc => {
    const docName = doc.name || doc.filename || '';
    const category = (doc.category || '').toUpperCase();
    const docType = doc.file_type || (docName.endsWith('.pdf') ? 'PDF' : docName.endsWith('.xlsx') || docName.endsWith('.csv') ? 'EXCEL' : docName.endsWith('.docx') ? 'DOCX' : 'OTHER');
    
    const matchesSearch = docName.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          category.toLowerCase().includes(searchTerm.toLowerCase());

    if (filterType === 'ALL') return matchesSearch;
    if (filterType === 'PDF') return matchesSearch && (docType === 'PDF' || docName.toLowerCase().endsWith('.pdf'));
    if (filterType === 'MANUAL') return matchesSearch && category === 'MANUAL';
    if (filterType === 'BLUEPRINT') return matchesSearch && category === 'BLUEPRINT';
    if (filterType === 'REPORT') return matchesSearch && (category === 'REPORT' || category === 'LOG');
    if (filterType === 'EXCEL') return matchesSearch && (docType === 'EXCEL' || docName.toLowerCase().endsWith('.xlsx') || docName.toLowerCase().endsWith('.csv'));
    
    return matchesSearch && docType.toUpperCase() === filterType.toUpperCase();
  }).sort((a, b) => {
    if (sortBy === 'name') {
      return (a.name || a.filename || '').localeCompare(b.name || b.filename || '');
    }
    if (sortBy === 'size') {
      return (b.size_bytes || 0) - (a.size_bytes || 0);
    }
    // Default: recent
    return new Date(b.uploaded_at || 0) - new Date(a.uploaded_at || 0);
  });

  // Handle Single Document Deletion
  const handleDeleteDocument = async (doc) => {
    const docId = doc._id || doc.id || doc.name || doc.filename;
    const docName = doc.name || doc.filename;

    if (!window.confirm(`Are you sure you want to delete "${docName}"?\n\nThis will remove the file from storage and clean up its vector index from FAISS.`)) {
      return;
    }

    setDeletingId(docId);
    try {
      await apiClient.deleteDocument(docId);
      showNotification(`Deleted "${docName}" from storage and FAISS vector index.`);
      setSelectedDocIds(prev => prev.filter(id => id !== docId));
      if (onRefresh) onRefresh();
      loadStats();
    } catch (err) {
      showNotification(`Failed to delete "${docName}": ${err.message}`, 'error');
    } finally {
      setDeletingId(null);
    }
  };

  // Handle Bulk Deletion
  const handleBulkDelete = async () => {
    if (selectedDocIds.length === 0) return;

    if (!window.confirm(`Are you sure you want to delete ${selectedDocIds.length} selected document(s)?\n\nThis will permanently delete physical files and purge vector embeddings.`)) {
      return;
    }

    setIsBulkDeleting(true);
    try {
      await apiClient.bulkDeleteDocuments(selectedDocIds);
      showNotification(`Successfully deleted ${selectedDocIds.length} documents.`);
      setSelectedDocIds([]);
      if (onRefresh) onRefresh();
      loadStats();
    } catch (err) {
      showNotification(`Bulk deletion error: ${err.message}`, 'error');
    } finally {
      setIsBulkDeleting(false);
    }
  };

  // Select all or toggle selection
  const handleToggleSelectAll = () => {
    if (selectedDocIds.length === filteredDocs.length) {
      setSelectedDocIds([]);
    } else {
      setSelectedDocIds(filteredDocs.map(d => d._id || d.id || d.name || d.filename));
    }
  };

  const handleToggleSelectRow = (docId) => {
    setSelectedDocIds(prev => 
      prev.includes(docId) ? prev.filter(id => id !== docId) : [...prev, docId]
    );
  };

  return (
    <div className="card-widget animate-fade-in">
      {/* Storage Analytics Overview Bar */}
      <div className="doc-stats-grid">
        <div className="doc-stat-card">
          <div className="doc-stat-icon-wrapper" style={{ background: 'var(--amber-bg)', color: 'var(--amber-primary)' }}>
            <Layers size={18} />
          </div>
          <div>
            <span className="doc-stat-label">TOTAL DOCUMENTS</span>
            <div className="doc-stat-value">{stats?.total_documents ?? documents.length} Files</div>
          </div>
        </div>

        <div className="doc-stat-card">
          <div className="doc-stat-icon-wrapper" style={{ background: 'var(--cyan-bg)', color: 'var(--cyan-primary)' }}>
            <HardDrive size={18} />
          </div>
          <div>
            <span className="doc-stat-label">STORAGE CONSUMED</span>
            <div className="doc-stat-value">{stats?.total_size_formatted || '0 KB'}</div>
          </div>
        </div>

        <div className="doc-stat-card">
          <div className="doc-stat-icon-wrapper" style={{ background: 'var(--emerald-bg)', color: 'var(--emerald-primary)' }}>
            <FileCheck size={18} />
          </div>
          <div>
            <span className="doc-stat-label">PDF MANUALS & SPECS</span>
            <div className="doc-stat-value">
              {stats?.pdf_count ?? documents.filter(d => (d.name || '').endsWith('.pdf')).length} PDFs
            </div>
          </div>
        </div>

        <div className="doc-stat-card">
          <div className="doc-stat-icon-wrapper" style={{ background: 'rgba(139, 92, 246, 0.12)', color: 'var(--violet-primary)' }}>
            <ShieldCheck size={18} />
          </div>
          <div>
            <span className="doc-stat-label">INDEXED IN RAG</span>
            <div className="doc-stat-value" style={{ color: 'var(--emerald-primary)' }}>100% Vectorized</div>
          </div>
        </div>
      </div>

      {/* Header & Filter Controls */}
      <div className="card-widget-head" style={{ marginTop: '20px' }}>
        <h3 style={{ fontSize: '15px', color: '#ffffff', display: 'flex', alignItems: 'center', gap: '8px' }}>
          Document Vault Repository ({filteredDocs.length})
        </h3>
        
        {/* Preset Category Chips */}
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {[
            { id: 'ALL', label: 'All Files' },
            { id: 'PDF', label: 'PDFs' },
            { id: 'MANUAL', label: 'Manuals' },
            { id: 'BLUEPRINT', label: 'Blueprints' },
            { id: 'REPORT', label: 'Reports & Logs' },
            { id: 'EXCEL', label: 'Excel/CSV' }
          ].map(t => (
            <button
              key={t.id}
              className="preset-chip-btn"
              style={{
                borderColor: filterType === t.id ? 'var(--amber-primary)' : 'var(--border-subtle)',
                color: filterType === t.id ? '#ffffff' : 'var(--text-secondary)',
                background: filterType === t.id ? 'var(--amber-bg)' : 'var(--bg-surface)',
                fontSize: '11.5px',
                padding: '4px 10px'
              }}
              onClick={() => setFilterType(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Search & Sort Toolbar */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--bg-core)', padding: '8px 12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-base)', flex: 1, minWidth: '220px' }}>
          <Search size={14} style={{ color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search by document name, OEM spec, or category..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ background: 'transparent', color: '#ffffff', width: '100%', fontSize: '12.5px' }}
          />
        </div>

        {/* Sort Select */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>SORT:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            style={{
              background: 'var(--bg-core)',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border-base)',
              padding: '6px 10px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '12px',
              cursor: 'pointer'
            }}
          >
            <option value="recent">Most Recent</option>
            <option value="name">Name (A-Z)</option>
            <option value="size">File Size</option>
          </select>
        </div>

        <button
          onClick={() => { if (onRefresh) onRefresh(); loadStats(); }}
          className="preset-chip-btn"
          title="Refresh List"
          style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '7px 12px' }}
        >
          <RefreshCw size={13} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Bulk Action Bar (when items selected, Engineer only) */}
      {canDelete && selectedDocIds.length > 0 && (
        <div className="bulk-actions-toolbar animate-fade-in">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckSquare size={16} style={{ color: 'var(--amber-primary)' }} />
            <span style={{ fontSize: '12.5px', color: '#ffffff', fontWeight: 600 }}>
              {selectedDocIds.length} document{selectedDocIds.length > 1 ? 's' : ''} selected
            </span>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => setSelectedDocIds([])}
              className="preset-chip-btn"
              style={{ fontSize: '11.5px' }}
            >
              Deselect All
            </button>
            <button
              onClick={handleBulkDelete}
              disabled={isBulkDeleting}
              className="preset-chip-btn"
              style={{
                background: 'rgba(244, 63, 94, 0.15)',
                borderColor: 'rgba(244, 63, 94, 0.4)',
                color: 'var(--rose-primary)',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '11.5px',
                fontWeight: 600
              }}
            >
              <Trash2 size={13} />
              {isBulkDeleting ? 'Deleting...' : `Delete Selected (${selectedDocIds.length})`}
            </button>
          </div>
        </div>
      )}

      {/* Documents Table */}
      <div style={{ overflowX: 'auto' }}>
        {filteredDocs.length === 0 ? (
          <div className="empty-vault-state">
            <div className="empty-vault-icon">
              <FolderOpen size={28} />
            </div>
            <div className="empty-vault-title">No Documents Found</div>
            <div className="empty-vault-sub">
              {documents.length === 0
                ? 'Upload technical reports, OEM manuals, or shift logs via the uploader above to begin indexing.'
                : 'No documents match your current filter criteria. Try adjusting the category or search term.'}
            </div>
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12.5px', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '10.5px' }}>
                {canDelete && (
                  <th style={{ padding: '8px 12px', width: '36px' }}>
                    <button 
                      onClick={handleToggleSelectAll} 
                      style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}
                    >
                      {selectedDocIds.length > 0 && selectedDocIds.length === filteredDocs.length ? (
                        <CheckSquare size={15} style={{ color: 'var(--amber-primary)' }} />
                      ) : (
                        <Square size={15} />
                      )}
                    </button>
                  </th>
                )}
                <th style={{ padding: '8px 12px' }}>DOCUMENT NAME</th>
                <th style={{ padding: '8px 12px' }}>CATEGORY / TYPE</th>
                <th style={{ padding: '8px 12px' }}>SIZE</th>
                <th style={{ padding: '8px 12px' }}>STATUS</th>
                <th style={{ padding: '8px 12px', textAlign: 'right' }}>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocs.map((doc, idx) => {
                const docId = doc._id || doc.id || doc.name || doc.filename || idx;
                const name = doc.name || doc.filename || `Document-${idx}`;
                const category = doc.category || doc.type || 'document';
                const size = doc.size || '-';
                const isSelected = selectedDocIds.includes(docId);
                const isDeleting = deletingId === docId;
                const isPdf = name.toLowerCase().endsWith('.pdf');

                return (
                  <tr 
                    key={docId}
                    className={`doc-table-row ${isSelected ? 'selected' : ''}`}
                    style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-primary)' }}
                  >
                    {/* Checkbox (Engineer only) */}
                    {canDelete && (
                      <td style={{ padding: '10px 12px' }}>
                        <button 
                          onClick={() => handleToggleSelectRow(docId)} 
                          style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: isSelected ? 'var(--amber-primary)' : 'var(--text-muted)', display: 'flex', alignItems: 'center' }}
                        >
                          {isSelected ? <CheckSquare size={15} /> : <Square size={15} />}
                        </button>
                      </td>
                    )}

                    {/* Name */}
                    <td style={{ padding: '10px 12px', fontWeight: 500 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <FileText size={15} style={{ color: isPdf ? 'var(--amber-primary)' : 'var(--cyan-primary)', flexShrink: 0 }} />
                        <span 
                          style={{ cursor: isPdf ? 'pointer' : 'default', textDecoration: isPdf ? 'underline dotted' : 'none' }}
                          onClick={() => isPdf && setPreviewDoc(doc)}
                          title={isPdf ? 'Click to preview PDF' : ''}
                        >
                          {name}
                        </span>
                      </div>
                    </td>

                    {/* Category + File Type */}
                    <td style={{ padding: '10px 12px', fontSize: '11px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--cyan-primary)', textTransform: 'uppercase' }}>
                          <span className="doc-category-badge">{category}</span>
                        </span>
                        {(() => {
                          const ext = name.split('.').pop()?.toLowerCase();
                          let chipClass = 'other';
                          let chipLabel = (ext || 'FILE').toUpperCase();
                          if (ext === 'pdf') chipClass = 'pdf';
                          else if (ext === 'xlsx' || ext === 'xls' || ext === 'csv') { chipClass = 'excel'; chipLabel = ext.toUpperCase(); }
                          else if (ext === 'docx' || ext === 'doc') chipClass = 'docx';
                          return <span className={`doc-type-chip ${chipClass}`}>{chipLabel}</span>;
                        })()}
                      </div>
                    </td>

                    {/* Size */}
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                      {size}
                    </td>

                    {/* Status */}
                    <td style={{ padding: '10px 12px' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', background: 'var(--emerald-bg)', color: 'var(--emerald-primary)', padding: '2px 7px', borderRadius: '4px', fontSize: '10.5px', fontFamily: 'var(--font-mono)', border: '1px solid rgba(16,185,129,0.3)' }}>
                        <CheckCircle2 size={10} />
                        {doc.status || 'Indexed in RAG'}
                      </span>
                    </td>

                    {/* Action Buttons */}
                    <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '6px' }}>
                        {/* Preview Action */}
                        <button
                          onClick={() => setPreviewDoc(doc)}
                          className="doc-action-btn"
                          title="Preview Document"
                        >
                          <Eye size={14} />
                        </button>

                        {/* Download Action */}
                        <a
                          href={apiClient.getDocumentDownloadUrl(name)}
                          download={name}
                          className="doc-action-btn"
                          title="Download File"
                        >
                          <Download size={14} />
                        </a>

                        {/* Delete Action — Chief Engineer Clearance Only */}
                        {canDelete && (
                          <button
                            onClick={() => handleDeleteDocument(doc)}
                            disabled={isDeleting}
                            className="doc-action-btn delete"
                            title="Delete Document & Purge Vectors (Chief Engineer Only)"
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* In-App PDF Preview Modal */}
      {previewDoc && (
        <PdfViewerModal
          document={previewDoc}
          onClose={() => setPreviewDoc(null)}
        />
      )}
    </div>
  );
};
