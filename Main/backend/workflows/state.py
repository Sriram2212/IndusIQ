"""
State definitions for LangGraph Agentic Workflows.
"""
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class QueryWorkflowState(TypedDict, total=False):
    """
    State passed through the Query Agentic Workflow.
    """
    question: str
    user_role: Optional[str]
    raw_entities: List[str]
    intents: List[Any]
    sub_questions: List[str]
    canonical_entities: List[Dict[str, Any]]
    vector_results: List[Any]
    graph_results: List[Any]
    contradictions: List[str]
    validation_report: Dict[str, Any]
    hop_count: int
    answer: str
    sources: List[Dict[str, Any]]
    key_entities: List[str]
    follow_up_suggestions: List[str]
    confidence: float
    formatted_graph_relations: List[str]
    error: Optional[str]


class IngestionWorkflowState(TypedDict, total=False):
    """
    State passed through the Document Ingestion Workflow.
    """
    file_path: str
    document_name: str
    pages: List[Dict[str, Any]]
    knowledge: List[Dict[str, Any]]
    chunks_data: List[Dict[str, Any]]
    graph_stored: bool
    vector_stored: bool
    status: str
    error: Optional[str]
