from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class QueryRequest(BaseModel):
    """Request model for the /query endpoint."""
    question: str


class SourceReference(BaseModel):
    """A single source citation in the query response."""
    type:     Optional[str] = "document"
    document: Optional[str] = None
    name:     Optional[str] = None
    page:     Optional[int] = None
    section:  Optional[str] = None
    detail:   Optional[str] = None
    verified: Optional[bool] = None


class CanonicalEntityRef(BaseModel):
    """A canonical entity in the response."""
    entity_id: str
    name:      str
    type:      str


class EvidenceFinding(BaseModel):
    """A single evidence finding from the validation step."""
    claim:         Optional[str] = None
    evidence_type: Optional[str] = None
    source:        Optional[str] = None


class QueryResponse(BaseModel):
    """Response model for the /query endpoint."""
    answer:                   str
    confidence:               float
    sources:                  List[SourceReference]         = []
    graph_context:            List[str]                     = []
    key_entities:             List[str]                     = []
    follow_up_suggestions:    Optional[List[str]]           = []
    evidence_classification:  Optional[List[Dict[str, Any]]] = []
    contradictions:           Optional[List[str]]           = []
    canonical_entities:       Optional[List[CanonicalEntityRef]] = []
    sub_questions:            Optional[List[str]]           = []
