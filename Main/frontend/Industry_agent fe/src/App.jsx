import React, { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import { apiClient } from './api/client';

import { Topbar } from './components/Topbar';
import { Sidebar } from './components/Sidebar';
import { QueryInput } from './components/QueryHub/QueryInput';
import { LangGraphTrace } from './components/QueryHub/LangGraphTrace';
import { AnswerCard } from './components/QueryHub/AnswerCard';
import { EquipmentCard } from './components/QueryHub/EquipmentCard';
import { EvidenceTrace } from './components/QueryHub/EvidenceTrace';
import { GraphCanvas } from './components/GraphExplorer/GraphCanvas';
import { DocumentUploader } from './components/DocumentVault/DocumentUploader';
import { DocumentList } from './components/DocumentVault/DocumentList';
import { SystemHealth } from './components/Telemetry/SystemHealth';
import { LoginScreen } from './components/LoginScreen';

export function App() {
  // Authentication session state
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("active_user");
    return saved ? JSON.parse(saved) : null;
  });

  const [activeTab, setActiveTab] = useState('query');
  const [isOnline, setIsOnline] = useState(false);
  const [currentQuery, setCurrentQuery] = useState('');
  const [responseData, setResponseData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState('');
  const [highlightedDoc, setHighlightedDoc] = useState(null);

  // User Role Clearances
  const [userRole, setUserRole] = useState(localStorage.getItem("user_role") || "engineer");
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // MongoDB Chat History States
  const [chatSessions, setChatSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [assets, setAssets] = useState([]);

  // Auto-scroll ref — pinned to bottom of chat thread
  const chatBottomRef = useRef(null);
  const queryInputRef = useRef(null);

  // Scroll to bottom whenever chatHistory updates or loading changes
  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [chatHistory, loading]);

  // Check health on mount + poll every 10s so OFFLINE auto-recovers
  useEffect(() => {
    checkBackendHealth();
    const healthInterval = setInterval(checkBackendHealth, 10000);
    return () => clearInterval(healthInterval);
  }, []);

  useEffect(() => {
    if (user) {
      loadChatSessions();
      loadAssets();
    }
  }, [user]);

  // Fetch documents and reset context when clearance level switches
  useEffect(() => {
    if (user) {
      loadDocuments();
      loadChatSessions();
      loadAssets();
    }
  }, [userRole, user]);

  const checkBackendHealth = async () => {
    const health = await apiClient.checkHealth();
    setIsOnline(health.status === 'healthy');
  };

  const loadDocuments = async () => {
    const docs = await apiClient.getDocuments();
    setDocuments(docs);
  };

  const loadAssets = async () => {
    const assetList = await apiClient.getAssets();
    setAssets(assetList);
  };

  const loadChatSessions = async () => {
    const sessions = await apiClient.getChatSessions();
    setChatSessions(sessions);
  };

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    localStorage.setItem("active_user", JSON.stringify(userData));
    setUserRole(userData.role);
    localStorage.setItem("user_role", userData.role);
  };

  const handleLogout = () => {
    localStorage.removeItem("active_user");
    localStorage.removeItem("user_role");
    setUser(null);
    setUserRole("engineer");
    handleNewChat();
  };

  const handleRoleChange = (newRole) => {
    localStorage.setItem("user_role", newRole);
    setUserRole(newRole);
    handleNewChat(); // Clear session to prevent query leakage between clearance roles
  };

  const handleSelectSession = async (sessionId) => {
    setCurrentSessionId(sessionId);
    setLoading(true);
    // Navigate to query tab so user sees the history
    setActiveTab('query');
    try {
      const history = await apiClient.getChatHistory(sessionId);
      setChatHistory(history);

      // Restore the last assistant response data for EvidenceTrace
      const assistantMsgs = history.filter(m => m.role === 'assistant');
      if (assistantMsgs.length > 0) {
        const lastMsg = assistantMsgs[assistantMsgs.length - 1];
        setResponseData(lastMsg.response_data || null);
      } else {
        setResponseData(null);
      }
    } catch (err) {
      console.error("Error loading chat history:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setChatHistory([]);
    setResponseData(null);
    setCurrentQuery('');
  };

  const handleDeleteSession = async (sessionId) => {
    await apiClient.deleteChatSession(sessionId);
    loadChatSessions();
    if (currentSessionId === sessionId) {
      handleNewChat();
    }
  };

  const handleExecuteQuery = useCallback(async (queryText) => {
    if (!queryText.trim()) return;
    setCurrentQuery(queryText);
    setLoading(true);
    // Ensure we're on the query tab
    setActiveTab('query');

    const tempUserMsg = {
      role: 'user',
      content: queryText,
      timestamp: new Date().toISOString()
    };
    setChatHistory(prev => [...prev, tempUserMsg]);

    try {
      const result = await apiClient.sendChatMessage(currentSessionId, queryText);

      const resp = result?.response || result;
      const answerText = resp?.answer || result?.answer || "No response received.";

      if (result?.session_id && !currentSessionId) {
        setCurrentSessionId(result.session_id);
      }

      const assistantMsg = {
        role: 'assistant',
        content: answerText,
        response_data: resp,
        timestamp: new Date().toISOString()
      };
      setChatHistory(prev => [...prev, assistantMsg]);
      setResponseData(resp);
      loadChatSessions();
    } catch (err) {
      console.error("Query execution error:", err);
      const errorMsg = {
        role: 'assistant',
        content: `Error executing query: ${err.message || 'Unable to connect to backend service.'}`,
        response_data: {
          answer: `Error executing query: ${err.message || 'Unable to connect to backend service.'}`,
          confidence: 0,
          sources: [],
          follow_up_suggestions: []
        },
        timestamp: new Date().toISOString()
      };
      setChatHistory(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  }, [currentSessionId]);

  const handleUploadSuccess = (newDoc) => {
    loadDocuments();
  };

  // If not signed in, render the login card screen
  if (!user) {
    return <LoginScreen onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="app-container">
      {/* Top Bar */}
      <Topbar
        userRole={userRole}
        fullName={user.full_name}
        isOnline={isOnline}
        onLogout={handleLogout}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
      />

      {/* Main Grid Body */}
      <div className={`app-body ${activeTab !== 'query' ? 'no-trace' : ''} ${isSidebarOpen ? '' : 'sidebar-collapsed'}`}>
        {/* Left Sidebar */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          docCount={documents.length}
          selectedAsset={selectedAsset}
          onSelectAsset={(assetName) => {
            setSelectedAsset(assetName);
            handleExecuteQuery(`What is the operational status, history, and telemetry for ${assetName}?`);
          }}
          chatSessions={chatSessions}
          currentSessionId={currentSessionId}
          onSelectSession={handleSelectSession}
          onNewChat={handleNewChat}
          onDeleteSession={handleDeleteSession}
          isSidebarOpen={isSidebarOpen}
          assets={assets}
          userRole={userRole}
        />

        {/* Center Main Viewport */}
        <main className="main-view-container" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflowY: 'auto' }}>
          {activeTab === 'query' && (
            <>
              {/* Query Hero */}
              <QueryInput
                onSearch={handleExecuteQuery}
                loading={loading}
                currentQuery={currentQuery}
                documents={documents}
                assets={assets}
              />

              {/* LangGraph Agentic Stepper — compact, only shown during loading or right after response */}
              <LangGraphTrace
                loading={loading}
                hasResponse={!!responseData}
              />

              {/* Chat thread list */}
              <div className="chat-thread-container">
                {chatHistory.length === 0 && !loading ? (
                  <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
                    <h3 style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>Ask the Industrial Copilot</h3>
                    <p style={{ fontSize: '13px' }}>Upload a PDF in the Vault tab, then type a question about it here.</p>
                  </div>
                ) : (
                  chatHistory.map((msg, index) => {
                    const isLastAssistant = msg.role === 'assistant' && index === chatHistory.length - 1;
                    // Only show EquipmentCard on last assistant message with meaningful (non-UNKNOWN) entities
                    const equipEnts = isLastAssistant
                      ? (msg.response_data?.canonical_entities || msg.response_data?.key_entities || [])
                      : [];
                    const meaningfulEnts = equipEnts.filter(e => {
                      const type = typeof e === 'object' ? (e.type || '') : '';
                      return type && type !== 'UNKNOWN' && type !== 'ENTITY';
                    });
                    return (
                      <div key={index} className={`chat-message-bubble ${msg.role}`}>
                        {msg.role === 'user' ? (
                          <div className="user-bubble-content">
                            {msg.content}
                            <div style={{ textAlign: 'right', marginTop: '4px' }}>
                              <span className="message-timestamp">
                                {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                              </span>
                            </div>
                          </div>
                        ) : (
                          <div style={{ width: '100%' }}>
                            <AnswerCard
                              responseData={msg.response_data}
                              fallbackContent={msg.content}
                              onSelectFollowUp={handleExecuteQuery}
                              onHighlightSource={setHighlightedDoc}
                            />
                            {/* Inline equipment context - only when meaningful entities exist */}
                            {isLastAssistant && msg.response_data?.equipment && (
                              <EquipmentCard
                                equipment={msg.response_data.equipment}
                                entities={[]}
                              />
                            )}
                            {isLastAssistant && !msg.response_data?.equipment && meaningfulEnts.length > 0 && (
                              <EquipmentCard
                                equipment={null}
                                entities={meaningfulEnts}
                              />
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })
                )}

                {/* Typing indicator while loading */}
                {loading && (
                  <div className="chat-message-bubble assistant">
                    <div className="typing-indicator-bubble">
                      <div className="typing-dots">
                        <div className="typing-dot" />
                        <div className="typing-dot" />
                        <div className="typing-dot" />
                      </div>
                      <span className="typing-label">Analyzing documents & knowledge graph...</span>
                    </div>
                  </div>
                )}

                {/* Auto-scroll anchor */}
                <div ref={chatBottomRef} />
              </div>
            </>
          )}

          {activeTab === 'graph' && (
            <GraphCanvas
              userRole={userRole}
              documents={documents}
              onInvestigateIssue={(query) => {
                setActiveTab('query');
                handleExecuteQuery(query);
              }}
            />
          )}

          {activeTab === 'vault' && (
            <>
              <DocumentUploader userRole={userRole} onUploadSuccess={handleUploadSuccess} />
              <DocumentList userRole={userRole} documents={documents} onRefresh={loadDocuments} />
            </>
          )}

          {activeTab === 'telemetry' && (
            <SystemHealth isOnline={isOnline} docCount={documents.length} />
          )}
        </main>

        {/* Right Evidence Trace Sidebar (Active in Query mode) */}
        {activeTab === 'query' && (
          <EvidenceTrace
            sources={responseData?.sources || []}
            graphContext={responseData?.graph_context || []}
            highlightedDoc={highlightedDoc}
          />
        )}
      </div>
    </div>
  );
}

export default App;
