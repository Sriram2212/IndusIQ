/**
 * API client for communicating with the FastAPI backend.
 * Uses live backend endpoints without mock data fallbacks.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || (window.location.hostname === '127.0.0.1' ? 'http://127.0.0.1:8000' : 'http://localhost:8000');

// Helper to extract active user role for RBAC routing
const getRoleHeader = () => {
  const role = localStorage.getItem("user_role") || "engineer";
  return { "X-User-Role": role };
};

export const apiClient = {
  /**
   * Check backend connectivity health
   */
  async checkHealth() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: "GET",
        headers: { 
          "Content-Type": "application/json",
          ...getRoleHeader()
        }
      });
      if (!response.ok) throw new Error("Health check failed");
      return await response.json();
    } catch (err) {
      console.warn("Backend health check failed:", err);
      return { status: "offline", error: err.message };
    }
  },

  /**
   * Submit natural language query to the LangGraph Copilot
   */
  async queryCopilot(question) {
    const response = await fetch(`${API_BASE_URL}/query`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        ...getRoleHeader()
      },
      body: JSON.stringify({ question })
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Query failed with status ${response.status}: ${errText}`);
    }

    return await response.json();
  },

  /**
   * Get dynamic list of documents filtered by role clearance
   */
  async getDocuments() {
    try {
      const response = await fetch(`${API_BASE_URL}/documents`, {
        method: "GET",
        headers: { 
          "Content-Type": "application/json",
          ...getRoleHeader()
        }
      });
      if (!response.ok) throw new Error("Failed to fetch documents");
      return await response.json();
    } catch (err) {
      console.error("Fetch documents failed:", err);
      return [];
    }
  },

  /**
   * Fetch live storage stats
   */
  async getDocumentStats() {
    try {
      const response = await fetch(`${API_BASE_URL}/documents/stats`, {
        method: "GET",
        headers: { 
          "Content-Type": "application/json",
          ...getRoleHeader()
        }
      });
      if (!response.ok) throw new Error("Failed to fetch document stats");
      return await response.json();
    } catch (err) {
      console.error("Fetch document stats failed:", err);
      return null;
    }
  },

  /**
   * Upload a single document to the LangGraph ingestion pipeline
   */
  async uploadDocument(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: "POST",
      headers: {
        ...getRoleHeader()
      },
      body: formData
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Upload failed with status ${response.status}: ${errText}`);
    }

    return await response.json();
  },

  /**
   * Upload multiple documents in a single request
   */
  async uploadBatchDocuments(files) {
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }

    const response = await fetch(`${API_BASE_URL}/documents/upload-batch`, {
      method: "POST",
      headers: {
        ...getRoleHeader()
      },
      body: formData
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Batch upload failed with status ${response.status}: ${errText}`);
    }

    return await response.json();
  },

  /**
   * Delete a document by ID or filename
   */
  async deleteDocument(docId) {
    const response = await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(docId)}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        ...getRoleHeader()
      }
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Delete failed: ${errText}`);
    }

    return await response.json();
  },

  /**
   * Bulk delete multiple documents
   */
  async bulkDeleteDocuments(docIds) {
    const response = await fetch(`${API_BASE_URL}/documents/bulk-delete`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getRoleHeader()
      },
      body: JSON.stringify({ doc_ids: docIds })
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Bulk delete failed: ${errText}`);
    }

    return await response.json();
  },

  /**
   * Get preview stream URL for in-app PDF viewing
   */
  getDocumentPreviewUrl(filename) {
    return `${API_BASE_URL}/documents/${encodeURIComponent(filename)}/preview`;
  },

  /**
   * Get download URL for document
   */
  getDocumentDownloadUrl(filename) {
    return `${API_BASE_URL}/documents/${encodeURIComponent(filename)}/download`;
  },

  /**
   * Fetch live Neo4j Knowledge Graph nodes and edges
   */
  async getGraphData(entity = null, limit = 80, document = null) {
    try {
      const url = new URL(`${API_BASE_URL}/graph/data`);
      if (entity) url.searchParams.append("entity", entity);
      if (document) url.searchParams.append("document", document);
      if (limit) url.searchParams.append("limit", limit.toString());

      const response = await fetch(url.toString(), {
        method: "GET",
        headers: { 
          "Content-Type": "application/json",
          ...getRoleHeader()
        }
      });

      if (!response.ok) throw new Error("Failed to fetch graph data");
      return await response.json();
    } catch (err) {
      console.error("Live graph fetch failed:", err);
      return null;
    }
  },

  /**
   * Fetch live Neo4j statistics
   */
  async getGraphStats() {
    try {
      const response = await fetch(`${API_BASE_URL}/graph/stats`, {
        method: "GET",
        headers: { 
          "Content-Type": "application/json",
          ...getRoleHeader()
        }
      });

      if (!response.ok) throw new Error("Failed to fetch graph stats");
      return await response.json();
    } catch (err) {
      console.error("Live graph stats fetch failed:", err);
      return null;
    }
  },

  /**
   * Fetch dynamic plant assets discovered from the graph
   */
  async getAssets() {
    try {
      const response = await fetch(`${API_BASE_URL}/graph/assets`, {
        method: "GET",
        headers: { 
          "Content-Type": "application/json",
          ...getRoleHeader()
        }
      });
      if (!response.ok) return [];
      return await response.json();
    } catch (err) {
      console.error("Fetch assets failed:", err);
      return [];
    }
  },

  /**
   * Fetch list of chat sessions from MongoDB
   */
  async getChatSessions() {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/sessions`, {
        method: "GET",
        headers: { 
          "Content-Type": "application/json",
          ...getRoleHeader()
        }
      });
      if (!response.ok) throw new Error("Failed to fetch chat sessions");
      return await response.json();
    } catch (err) {
      console.error("Fetch chat sessions failed:", err);
      return [];
    }
  },

  /**
   * Fetch chat history for a session from MongoDB
   */
  async getChatHistory(sessionId) {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/history/${sessionId}`, {
        method: "GET",
        headers: { 
          "Content-Type": "application/json",
          ...getRoleHeader()
        }
      });
      if (!response.ok) throw new Error("Failed to fetch chat history");
      return await response.json();
    } catch (err) {
      console.error(`Fetch history for session ${sessionId} failed:`, err);
      return [];
    }
  },

  /**
   * Send a chat message and save to MongoDB
   */
  async sendChatMessage(sessionId, message) {
    const response = await fetch(`${API_BASE_URL}/chat/message`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        ...getRoleHeader()
      },
      body: JSON.stringify({ session_id: sessionId, message })
    });
    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Failed to send chat message (${response.status}): ${errText}`);
    }
    return await response.json();
  },

  /**
   * Delete a chat session and its history
   */
  async deleteChatSession(sessionId) {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/sessions/${sessionId}`, {
        method: "DELETE",
        headers: { 
          "Content-Type": "application/json",
          ...getRoleHeader()
        }
      });
      if (!response.ok) throw new Error("Failed to delete session");
      return await response.json();
    } catch (err) {
      console.error(`Delete session ${sessionId} failed:`, err);
      return { status: "error", message: err.message };
    }
  },

  /**
   * Submit credentials to login user and assign clearance roles
   */
  async login(username, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    if (!response.ok) {
      const errorDetail = await response.json().catch(() => ({}));
      throw new Error(errorDetail.detail || "Authentication failed");
    }
    return await response.json();
  }
};
