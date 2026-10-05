"""
Document Processing Pipeline — LangGraph Orchestrated
======================================================
Coordinates document ingestion, chunking, LLM knowledge extraction,
Neo4j Knowledge Graph persistence, and FAISS Vector Store persistence via LangGraph.
"""

from typing import Any, Dict, List
from backend.workflows.ingestion_workflow import create_ingestion_workflow


class ProcessingPipeline:
    """
    Orchestrates end-to-end document processing via a compiled LangGraph StateGraph.
    """

    def __init__(self):
        print("[INFO] Initializing ProcessingPipeline with LangGraph workflow...")
        self.workflow = create_ingestion_workflow()
        print("[OK] LangGraph Ingestion Workflow compiled.")

    def process(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Process a file path through the LangGraph Ingestion StateGraph.
        Returns the extracted knowledge list.
        """
        print(f"\n================ LANGGRAPH INGESTION PIPELINE STARTED ================")
        print(f"File Path: {file_path}")

        initial_state = {
            "file_path": file_path,
            "document_name": "",
            "pages": [],
            "knowledge": [],
            "chunks_data": [],
            "graph_stored": False,
            "vector_stored": False,
            "status": "started",
            "error": None,
        }

        final_state = self.workflow.invoke(initial_state)

        print(f"Status: {final_state.get('status')}")
        print(f"================ LANGGRAPH INGESTION PIPELINE COMPLETED ================\n")

        return final_state.get("knowledge", [])