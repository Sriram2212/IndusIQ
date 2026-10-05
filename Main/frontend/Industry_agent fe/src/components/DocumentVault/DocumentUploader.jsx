import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, Loader2, CheckCircle2, AlertCircle, Sparkles, Files, X, Plus } from 'lucide-react';
import { apiClient } from '../../api/client';
import { useToast } from '../Toast';

const INGESTION_STAGES = [
  '1. Parsing Document & Page Metadata',
  '2. Semantic Text Chunking',
  '3. LLM Knowledge Extraction (Entities & Relations)',
  '4. Neo4j Knowledge Graph Persistence',
  '5. FAISS Vector Store Embedding'
];

export const DocumentUploader = ({ onUploadSuccess, userRole = 'engineer' }) => {
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadQueue, setUploadQueue] = useState([]);
  const [activeFileIndex, setActiveFileIndex] = useState(0);
  const [currentStage, setCurrentStage] = useState(0);
  const [overallSummary, setOverallSummary] = useState(null);
  const fileInputRef = useRef(null);
  const toast = useToast();

  const isOperator = (userRole || '').toLowerCase() === 'operator';

  const handleFileDrop = async (e) => {
    e.preventDefault();
    setDragOver(false);
    const rawFiles = e.dataTransfer ? e.dataTransfer.files : e.target.files;
    if (rawFiles && rawFiles.length > 0) {
      const fileList = Array.from(rawFiles);
      await processMultipleFiles(fileList);
    }
  };

  const processMultipleFiles = async (fileList) => {
    if (fileList.length === 0) return;

    setUploading(true);
    setOverallSummary(null);

    toast.info(
      'Document Ingestion Initiated',
      `Queued ${fileList.length} file${fileList.length > 1 ? 's' : ''} for LangGraph RAG pipeline processing.`
    );

    // Initialize queue items
    const queue = fileList.map((f, idx) => ({
      id: `queue-${Date.now()}-${idx}`,
      file: f,
      name: f.name,
      sizeFormatted: f.size > 1024 * 1024 ? `${(f.size / (1024 * 1024)).toFixed(1)} MB` : `${Math.round(f.size / 1024)} KB`,
      status: 'pending', // 'pending' | 'processing' | 'success' | 'error'
      stageIndex: 0,
      errorMessage: null,
      extractedCount: 0
    }));

    setUploadQueue(queue);

    let successCount = 0;
    let failCount = 0;

    for (let i = 0; i < queue.length; i++) {
      setActiveFileIndex(i);
      setCurrentStage(0);

      // Update current item status to processing
      setUploadQueue(prev => prev.map((item, idx) => idx === i ? { ...item, status: 'processing' } : item));

      // Simulate progressive stage feedback for LangGraph ingestion
      const stageInterval = setInterval(() => {
        setCurrentStage((prev) => (prev < 4 ? prev + 1 : prev));
      }, 800);

      try {
        const res = await apiClient.uploadDocument(queue[i].file);
        clearInterval(stageInterval);
        setCurrentStage(4);
        successCount++;

        const extracted = res.knowledge_extracted?.length || res.chunks || 1;

        setUploadQueue(prev => prev.map((item, idx) => 
          idx === i 
            ? { ...item, status: 'success', stageIndex: 5, extractedCount: extracted } 
            : item
        ));

        toast.success(
          'Document Indexed Successfully',
          `"${queue[i].name}" processed (${extracted} knowledge chunks extracted) into FAISS & Knowledge Graph.`
        );

        if (onUploadSuccess) {
          onUploadSuccess({
            id: res.id || `DOC-${Date.now()}-${i}`,
            name: queue[i].name,
            type: queue[i].name.split('.').pop().toUpperCase(),
            size: queue[i].sizeFormatted,
            chunks: extracted,
            status: 'Indexed in Neo4j & FAISS'
          });
        }
      } catch (err) {
        clearInterval(stageInterval);
        failCount++;
        const errorMsg = err.message || 'Ingestion pipeline error';
        setUploadQueue(prev => prev.map((item, idx) => 
          idx === i 
            ? { ...item, status: 'error', errorMessage: errorMsg } 
            : item
        ));

        toast.error(
          'Document Upload Failed',
          `Failed to process "${queue[i].name}": ${errorMsg}`
        );
      }

      // Small pause between multiple files for smooth UI transition
      await new Promise(r => setTimeout(r, 400));
    }

    setUploading(false);
    setOverallSummary({
      total: queue.length,
      success: successCount,
      failed: failCount
    });

    if (queue.length > 1) {
      if (failCount === 0) {
        toast.success('Batch Processing Complete', `All ${successCount} files were successfully indexed.`);
      } else {
        toast.warning('Batch Processing Finished', `${successCount} succeeded, ${failCount} failed.`);
      }
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const clearQueue = () => {
    setUploadQueue([]);
    setOverallSummary(null);
  };

  const activeFile = uploadQueue[activeFileIndex];

  if (isOperator) {
    return (
      <div className="card-widget animate-fade-in" style={{ marginBottom: '24px', background: 'rgba(245, 158, 11, 0.04)', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '8px 4px' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'var(--amber-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--amber-primary)', flexShrink: 0 }}>
            <Files size={20} />
          </div>
          <div>
            <h4 style={{ fontSize: '14px', color: '#ffffff', marginBottom: '2px' }}>Document Ingestion — Read-Only Mode (Operator Clearance)</h4>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Plant Operators have monitoring and query clearance. Document uploads and knowledge graph indexing are restricted to <strong>Chief Engineers</strong> and <strong>Maintenance Technicians</strong>.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card-widget animate-fade-in" style={{ marginBottom: '24px' }}>
      <div className="card-widget-head">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Files size={18} style={{ color: 'var(--amber-primary)' }} />
          <h3 style={{ fontSize: '15px', color: '#ffffff' }}>Batch Document Ingestion</h3>
        </div>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--amber-primary)' }}>
          LANGGRAPH RAG PIPELINE
        </span>
      </div>

      {/* Drag & Drop Area supporting Multiple Files */}
      <div
        className={`upload-dropzone-box ${dragOver ? 'dragover' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleFileDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
      >
        <input 
          type="file" 
          ref={fileInputRef}
          style={{ display: 'none' }} 
          onChange={handleFileDrop}
          accept=".pdf,.docx,.xlsx,.xls,.csv,.png,.jpg,.jpeg"
          multiple
        />

        <div className="dropzone-icon-circle">
          {uploading ? <Loader2 size={26} className="animate-spin" /> : <UploadCloud size={26} />}
        </div>

        <h4 style={{ fontSize: '15.5px', color: '#ffffff', marginBottom: '6px' }}>
          {uploading 
            ? `Processing ${activeFileIndex + 1} of ${uploadQueue.length} files...` 
            : 'Click or Drag & Drop Multiple Industrial Files'}
        </h4>
        <p style={{ color: 'var(--text-muted)', fontSize: '12.5px', maxWidth: '520px', margin: '0 auto' }}>
          Drop single or batch PDFs, OEM Manuals, Blueprints, Maintenance Work Orders, or Shift Logs to index into Neo4j & FAISS.
        </p>

        <div className="file-type-badges" style={{ marginTop: '16px' }}>
          <span className="file-badge" style={{ color: 'var(--amber-primary)', borderColor: 'var(--amber-dim)' }}>PDF MANUALS</span>
          <span className="file-badge" style={{ color: 'var(--cyan-primary)', borderColor: 'rgba(6,182,212,0.3)' }}>BLUEPRINTS & SPECS</span>
          <span className="file-badge" style={{ color: 'var(--emerald-primary)', borderColor: 'rgba(16,185,129,0.3)' }}>EXCEL / LOGS</span>
          <span className="file-badge">DOCX / REPORTS</span>
        </div>
      </div>

      {/* Real-time Ingestion Progress for Active File */}
      {uploading && (
        <div style={{ marginTop: '16px', background: 'var(--bg-core)', padding: '14px 16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-base)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#ffffff' }}>
              Current File: <span style={{ color: 'var(--amber-primary)' }}>{activeFile?.name}</span>
            </span>
            <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--cyan-primary)' }}>
              STAGE {currentStage + 1}/5
            </span>
          </div>

          <div style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', marginBottom: '8px' }}>
            {INGESTION_STAGES[currentStage]}
          </div>

          <div style={{ width: '100%', height: '5px', background: 'var(--bg-surface-elevated)', borderRadius: '3px', overflow: 'hidden' }}>
            <div 
              style={{ 
                width: `${((currentStage + 1) / 5) * 100}%`, 
                height: '100%', 
                background: 'linear-gradient(90deg, var(--amber-primary), var(--cyan-primary), var(--emerald-primary))', 
                transition: 'width 0.4s ease' 
              }} 
            />
          </div>
        </div>
      )}

      {/* Batch Upload Queue List */}
      {uploadQueue.length > 0 && (
        <div style={{ marginTop: '18px', background: 'var(--bg-core)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', padding: '14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
              BATCH QUEUE ({uploadQueue.length} FILES)
            </span>
            {!uploading && (
              <button 
                onClick={clearQueue} 
                className="preset-chip-btn" 
                style={{ padding: '2px 8px', fontSize: '11px', color: 'var(--text-muted)' }}
              >
                Clear Queue
              </button>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '220px', overflowY: 'auto' }}>
            {uploadQueue.map((item, idx) => (
              <div 
                key={item.id || idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '8px 12px',
                  background: item.status === 'processing' ? 'rgba(245, 158, 11, 0.08)' : 'var(--bg-surface)',
                  borderRadius: 'var(--radius-sm)',
                  border: `1px solid ${item.status === 'processing' ? 'var(--amber-dim)' : 'var(--border-subtle)'}`
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
                  <FileText size={15} style={{ color: item.status === 'success' ? 'var(--emerald-primary)' : item.status === 'error' ? 'var(--rose-primary)' : 'var(--amber-primary)', flexShrink: 0 }} />
                  <span style={{ fontSize: '12.5px', color: 'var(--text-primary)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                    {item.name}
                  </span>
                  <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                    ({item.sizeFormatted})
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                  {item.status === 'pending' && (
                    <span style={{ fontSize: '10.5px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>Pending</span>
                  )}
                  {item.status === 'processing' && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10.5px', fontFamily: 'var(--font-mono)', color: 'var(--amber-primary)' }}>
                      <Loader2 size={11} className="animate-spin" /> Indexing...
                    </span>
                  )}
                  {item.status === 'success' && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10.5px', fontFamily: 'var(--font-mono)', color: 'var(--emerald-primary)' }}>
                      <CheckCircle2 size={12} /> Indexed ({item.extractedCount} Chunks)
                    </span>
                  )}
                  {item.status === 'error' && (
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10.5px', fontFamily: 'var(--font-mono)', color: 'var(--rose-primary)' }} title={item.errorMessage}>
                      <AlertCircle size={12} /> Failed
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Batch Summary Report */}
          {overallSummary && (
            <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '12px', color: overallSummary.failed === 0 ? 'var(--emerald-primary)' : 'var(--amber-primary)' }}>
                {overallSummary.success} of {overallSummary.total} files indexed successfully.
              </span>
              <button 
                onClick={() => fileInputRef.current?.click()} 
                className="preset-chip-btn"
                style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--amber-primary)', borderColor: 'var(--amber-dim)' }}
              >
                <Plus size={12} /> Add More Files
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
