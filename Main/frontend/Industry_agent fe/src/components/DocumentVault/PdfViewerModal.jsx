import React, { useState } from 'react';
import { X, ExternalLink, Download, FileText, Maximize2, Minimize2, AlertCircle } from 'lucide-react';
import { apiClient } from '../../api/client';

export const PdfViewerModal = ({ document, onClose }) => {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [loadError, setLoadError] = useState(false);

  if (!document) return null;

  const docName = document.name || document.filename || 'Document';
  const previewUrl = apiClient.getDocumentPreviewUrl(docName);
  const downloadUrl = apiClient.getDocumentDownloadUrl(docName);
  const isPdf = docName.toLowerCase().endsWith('.pdf');

  return (
    <div 
      className="pdf-modal-overlay" 
      onClick={(e) => {
        if (e.target.className === 'pdf-modal-overlay') onClose();
      }}
    >
      <div className={`pdf-modal-container ${isFullscreen ? 'fullscreen' : ''}`}>
        {/* Header Bar */}
        <div className="pdf-modal-header">
          <div className="pdf-modal-title-area">
            <div className="pdf-icon-badge">
              <FileText size={18} style={{ color: 'var(--amber-primary)' }} />
            </div>
            <div>
              <h3 className="pdf-modal-filename">{docName}</h3>
              <div className="pdf-modal-meta">
                <span className="pdf-meta-badge">{document.category || 'TECHNICAL DOC'}</span>
                <span className="pdf-meta-size">{document.size || ''}</span>
                {document.status && (
                  <span className="pdf-meta-status">{document.status}</span>
                )}
              </div>
            </div>
          </div>

          {/* Action Controls */}
          <div className="pdf-modal-actions">
            <a
              href={downloadUrl}
              download={docName}
              className="pdf-action-btn"
              title="Download File"
            >
              <Download size={15} />
              <span>Download</span>
            </a>

            <a
              href={previewUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="pdf-action-btn"
              title="Open in New Tab"
            >
              <ExternalLink size={15} />
              <span>Open Tab</span>
            </a>

            <button
              className="pdf-action-btn"
              onClick={() => setIsFullscreen(!isFullscreen)}
              title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
            >
              {isFullscreen ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
            </button>

            <button
              className="pdf-modal-close-btn"
              onClick={onClose}
              title="Close Preview"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* PDF / File Content Viewport */}
        <div className="pdf-modal-body">
          {loadError ? (
            <div className="pdf-error-container">
              <AlertCircle size={40} style={{ color: 'var(--rose-primary)', marginBottom: '12px' }} />
              <h4>Unable to preview "{docName}" directly</h4>
              <p>This file type or server configuration might require downloading.</p>
              <div style={{ marginTop: '16px', display: 'flex', gap: '12px' }}>
                <a href={downloadUrl} download={docName} className="preset-chip-btn" style={{ background: 'var(--amber-primary)', color: '#000' }}>
                  <Download size={14} style={{ marginRight: '6px' }} /> Download File
                </a>
                <a href={previewUrl} target="_blank" rel="noopener noreferrer" className="preset-chip-btn">
                  <ExternalLink size={14} style={{ marginRight: '6px' }} /> Try Direct Link
                </a>
              </div>
            </div>
          ) : isPdf ? (
            <iframe
              src={`${previewUrl}#toolbar=1&navpanes=1&scrollbar=1`}
              title={docName}
              className="pdf-iframe-viewer"
              onError={() => setLoadError(true)}
            />
          ) : (
            <div className="pdf-non-pdf-container">
              <FileText size={48} style={{ color: 'var(--cyan-primary)', marginBottom: '16px' }} />
              <h4>Non-PDF Industrial Document</h4>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', maxWidth: '400px', margin: '8px auto 20px' }}>
                {docName} is stored in your Document Vault. You can download and open it in its native application (Excel, Word, CAD, etc.).
              </p>
              <a href={downloadUrl} download={docName} className="preset-chip-btn" style={{ background: 'var(--amber-primary)', color: '#000' }}>
                <Download size={14} style={{ marginRight: '6px' }} /> Download {document.file_type || 'File'}
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
