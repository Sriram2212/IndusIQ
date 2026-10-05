# 🏭 IndusIQ: Industrial Agentic Knowledge Intelligence Platform

An enterprise-grade **Agentic Graph-RAG & Multi-Hop Reasoning System** for industrial plant operations, maintenance, and asset intelligence. Powered by **LangGraph**, **FastAPI**, **Neo4j Graph Database**, **FAISS Vector Embeddings**, **Google Gemini**, and a modern **React UI**.

---

## 🌟 Architecture & Capabilities

`
                  +----------------------------------------------+
                  |               Industrial User                |
                  |     (Chief Engineer / Tech / Operator)       |
                  +----------------------+-----------------------+
                                         |
                                         v
                  +----------------------------------------------+
                  |         React 18 + Vite Industrial UI        |
                  |   (QueryHub, Graph Explorer, Document Vault) |
                  +----------------------+-----------------------+
                                         | REST & SSE (Port 8000)
                                         v
                  +----------------------------------------------+
                  |            FastAPI Agentic Backend           |
                  +----------------------+-----------------------+
                                         |
                                         v
                  +----------------------------------------------+
                  |         LangGraph Orchestration Graph        |
                  |  1. Intent Extraction & Decompose            |
                  |  2. Canonical Entity Resolution              |
                  |  3. Hybrid Retrieval (Vector + Graph BFS)    |
                  |  4. Evidence Validation & Factuality Check   |
                  |  5. Cited Answer Generation with RBAC        |
                  |  6. Confidence Calibration & Citation Check  |
                  +-----------+----------------------+-----------+
                              |                      |
                              v                      v
                +--------------------------+  +--------------------------+
                |    Neo4j Graph Database  |  |    FAISS Vector Store    |
                | (Ontology: Equipment,    |  |  (Dense Semantic Chunks, |
                |  Components, Issues,     |  |   Cosine Similarity)     |
                |  Sensors, Processes)     |  +--------------------------+
                +--------------------------+
`

### ✨ Core Features

1. **🤖 LangGraph Agentic Pipeline**: Stateful multi-step reasoning that performs query decomposition, entity canonicalization, hybrid retrieval, dynamic BFS expansion, factuality validation, and citation verification.
2. **🕸️ PDF-Scoped Neo4j Knowledge Graph**: Real-time relational network displaying plant topology, equipment hierarchies, and inspection findings scoped to specific uploaded PDF reports.
3. **🚨 Instant Issue Isolation & Team Communication**: Dedicated fault/crack highlighting with 1-click Copilot diagnostic triggers and structured context copying for cross-team field communication.
4. **🔐 Role-Based Access Control (RBAC)**:
   * **Chief Engineer (engineer)**: Full access to all 10 ontology types, deep graph traversal, Cypher tools, and schema controls.
   * **Maintenance Technician (	echnician)**: Maintenance-focused view (Equipment, Component, Issue, Technician, Process).
   * **Plant Operator (operator)**: Telemetry & asset status view (Equipment, Location, Sensor).
5. **📑 Grounded Citation & RCA**: Provides clear, step-by-step remediation procedures, safety Lockout/Tagout (LOTO) protocols, and factuality tags.

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Agentic Workflow** | LangGraph, LangChain, Google Gemini |
| **Backend Framework**| Python 3.10+, FastAPI, Uvicorn, Pydantic v2 |
| **Knowledge Graph**  | Neo4j 5.x Graph Database, Cypher Query Language |
| **Vector Store**     | FAISS (Facebook AI Similarity Search), SentenceTransformers |
| **Database & Auth**  | MongoDB (Chat Session Persistence & RBAC Store) |
| **Frontend**         | React 18, Vite, Lucide Icons, Vanilla CSS Design System |

---

## 🚀 Getting Started

### 1. Prerequisites
* **Python**: 3.10 or higher
* **Node.js**: 18.x or higher (
pm included)
* **Neo4j**: 5.x (Desktop or Docker)
* **MongoDB**: 6.x or higher (Local or Docker)

---

### 2. Environment Configuration

Create your .env file from .env.example:

`ash
cp .env.example .env
cp .env.example Main/.env
`

Configure your .env variables:
`env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
GEMINI_API_KEY=your_gemini_api_key
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=industrial_intelligence
`

---

### 3. Start Database Services (Docker Quickstart)

`ash
# Start Neo4j
docker run -d \
  --name indus-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_neo4j_password \
  neo4j:5.26

# Start MongoDB
docker run -d \
  --name indus-mongo \
  -p 27017:27017 \
  mongo:7.0
`

---

### 4. Backend Setup & Startup

`ash
# Create & activate virtual environment
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
cd Main
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
`
Backend API will be running at http://localhost:8000 (API Docs: http://localhost:8000/docs).

---

### 5. Frontend Setup & Startup

Open a new terminal:

`ash
cd Main/frontend/Industry_agent\ fe

# Install dependencies
npm install

# Start Vite dev server
npm run dev
`
Frontend Web Application will be live at http://localhost:5173.

---

## 👥 Seed Accounts & Role Clearances

| Username | Password | Role | Clearance Level |
| :--- | :--- | :--- | :--- |
| kannan | engineer123 | **Chief Engineer** | Full System & Graph Access |
| suriya | 	ech123 | **Technician** | Maintenance, Components & Issues |
| operator1 | operator123 | **Operator** | Telemetry, Equipment & Sensors |

---

## 📁 Repository Structure

`
.
├── Main/
│   ├── backend/
│   │   ├── agents/          # LangGraph Ingestion & Query Agent nodes
│   │   ├── api/             # FastAPI REST endpoints (graph, chat, auth, documents)
│   │   ├── config/          # Environment & connection settings
│   │   ├── documents/       # Document ingestion, OCR, & text processing
│   │   ├── graph/           # Neo4j connection manager & Cypher executors
│   │   ├── pipeline/        # Ingestion & orchestration pipelines
│   │   ├── retrieval/       # Hybrid retriever (FAISS vector + Graph BFS)
│   │   ├── storage/         # MongoDB session & user stores
│   │   └── workflows/       # LangGraph StateGraph workflow builders
│   ├── frontend/
│   │   └── Industry_agent fe/ # React 18 + Vite Industrial UI
│   │       ├── src/components/
│   │       │   ├── QueryHub/       # AI Copilot, Stepper, Answer Cards
│   │       │   ├── GraphExplorer/  # PDF-Scoped Neo4j Knowledge Graph
│   │       │   ├── DocumentVault/  # PDF Upload & Management
│   │       │   └── Telemetry/      # Live System Health Monitor
│   │       └── src/api/            # Backend API client
│   └── sample_data/         # Industrial test PDF documents & uploads
├── .env.example             # Environment template
├── .gitignore               # Production gitignore rules
├── requirements.txt         # Python dependencies
└── README.md                # Project documentation
`

---

## 📄 License
This project is licensed under the MIT License.
