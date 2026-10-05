"""
LangGraph Document Ingestion Workflow.
Coordinates parsing, semantic chunking, entity-relation extraction,
Neo4j Knowledge Graph persistence, and FAISS Vector Store persistence as a stateful graph.
"""

import os
from typing import Any, Dict

from langgraph.graph import StateGraph, START, END

from backend.agents.ingestion_agent import IngestionAgent
from backend.agents.extraction_agent import ExtractionAgent
from backend.services.graph_service import GraphService
from backend.services.vector_service import VectorService
from backend.workflows.state import IngestionWorkflowState


class IngestionWorkflowBuilder:
    """
    Builder for compiling the LangGraph Document Ingestion Workflow.
    """

    def __init__(self):
        self.ingestion_agent = IngestionAgent()
        self.extraction_agent = ExtractionAgent()
        self.graph_service = GraphService()
        self.vector_service = VectorService()

    # ─────────────────────────────────────────────────────────────
    # Node 1: Ingest & Parse Document
    # ─────────────────────────────────────────────────────────────
    def ingest_document_node(self, state: IngestionWorkflowState) -> Dict[str, Any]:
        file_path = state.get("file_path", "")
        document_name = os.path.basename(file_path)
        print(f"\n[LANGGRAPH:INGEST_NODE] 1. Ingesting Document '{document_name}' from {file_path}")

        try:
            pages = self.ingestion_agent.ingest(file_path)
            print(f"   [OK] Ingested {len(pages)} page(s)")
            return {
                "document_name": document_name,
                "pages": pages,
            }
        except Exception as e:
            print(f"   [ERROR] Ingestion failed: {e}")
            return {
                "document_name": document_name,
                "pages": [],
                "error": str(e),
            }

    # ─────────────────────────────────────────────────────────────
    # Node 2: Semantic Chunk & Extract Knowledge
    # ─────────────────────────────────────────────────────────────
    def chunk_and_extract_node(self, state: IngestionWorkflowState) -> Dict[str, Any]:
        pages = state.get("pages", [])
        print(f"\n[LANGGRAPH:INGEST_NODE] 2. Chunking & Extracting Knowledge ({len(pages)} pages)")

        try:
            knowledge = self.extraction_agent.process(pages)
            print(f"   [OK] Extracted knowledge from {len(knowledge)} chunk(s)")

            chunks_data = [
                {
                    "text": item["chunk"],
                    "metadata": item["metadata"]
                }
                for item in knowledge
            ]
            return {
                "knowledge": knowledge,
                "chunks_data": chunks_data,
            }
        except Exception as e:
            print(f"   [ERROR] Chunk extraction failed: {e}")
            return {
                "knowledge": [],
                "chunks_data": [],
                "error": str(e),
            }

    # ─────────────────────────────────────────────────────────────
    # Node 3: Store in Neo4j Knowledge Graph
    # ─────────────────────────────────────────────────────────────
    def store_graph_node(self, state: IngestionWorkflowState) -> Dict[str, Any]:
        knowledge = state.get("knowledge", [])
        document_name = state.get("document_name", "")
        print(f"\n[LANGGRAPH:INGEST_NODE] 3. Storing {len(knowledge)} items in Neo4j Graph (doc: '{document_name}')")

        try:
            for chunk in knowledge:
                self.graph_service.store(chunk, document_name=document_name)
            print("   [OK] Stored in Neo4j Knowledge Graph")
            return {"graph_stored": True}
        except Exception as e:
            print(f"   [ERROR] Neo4j graph storage failed: {e}")
            return {"graph_stored": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────
    # Node 4: Store in FAISS Vector Store
    # ─────────────────────────────────────────────────────────────
    def store_vector_node(self, state: IngestionWorkflowState) -> Dict[str, Any]:
        chunks_data = state.get("chunks_data", [])
        document_name = state.get("document_name", "Unknown")
        print(f"\n[LANGGRAPH:INGEST_NODE] 4. Storing {len(chunks_data)} vectors in FAISS")

        try:
            self.vector_service.store_chunks(
                chunks_data,
                document_name
            )
            print("   [OK] Stored in FAISS Vector Store")
            return {"vector_stored": True}
        except Exception as e:
            print(f"   [ERROR] FAISS storage failed: {e}")
            return {"vector_stored": False, "error": str(e)}

    # ─────────────────────────────────────────────────────────────
    # Node 5: Finalize
    # ─────────────────────────────────────────────────────────────
    def finalize_node(self, state: IngestionWorkflowState) -> Dict[str, Any]:
        doc = state.get("document_name", "")
        graph_ok = state.get("graph_stored", False)
        vector_ok = state.get("vector_stored", False)
        err = state.get("error")

        print(f"\n[LANGGRAPH:INGEST_NODE] 5. Finalizing Ingestion for '{doc}'")
        if graph_ok and vector_ok:
            status = "processed and stored successfully"
        else:
            status = f"partial/failed storage (graph={graph_ok}, vector={vector_ok}, error={err})"

        print(f"   Status: {status}")
        return {"status": status}


def create_ingestion_workflow():
    """
    Assembles and compiles the Document Ingestion LangGraph StateGraph.
    """
    builder = IngestionWorkflowBuilder()
    workflow = StateGraph(IngestionWorkflowState)

    # Add Nodes
    workflow.add_node("ingest_document", builder.ingest_document_node)
    workflow.add_node("chunk_and_extract", builder.chunk_and_extract_node)
    workflow.add_node("store_graph", builder.store_graph_node)
    workflow.add_node("store_vector", builder.store_vector_node)
    workflow.add_node("finalize", builder.finalize_node)

    # Add Edges
    workflow.add_edge(START, "ingest_document")
    workflow.add_edge("ingest_document", "chunk_and_extract")
    workflow.add_edge("chunk_and_extract", "store_graph")
    workflow.add_edge("store_graph", "store_vector")
    workflow.add_edge("store_vector", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile()
