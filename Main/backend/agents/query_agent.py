"""
Query Agent (Expert Copilot) — LangGraph Orchestrated
======================================================
Agent 3 orchestrates multi-hop reasoning, entity extraction, canonicalization,
hybrid retrieval (reranked vectors + 3-tier graph traversal), contradiction detection,
evidence validation, corrective graph hops, grounded answer generation,
citation verification, and confidence calibration via LangGraph.
"""

from typing import Any, Dict
from backend.workflows.query_workflow import create_query_workflow


class QueryAgent:
    """
    Agent 3 — Query Agent (Expert Copilot).

    Powered by a compiled LangGraph StateGraph workflow that performs stateful,
    corrective, multi-step RAG reasoning with full observability.
    """

    def __init__(self):
        print("[INFO] Initializing QueryAgent with LangGraph workflow...")
        self.workflow = create_query_workflow()
        print("[OK] LangGraph Query Workflow compiled.")

    def query(self, question: str, user_role: str = "engineer") -> Dict[str, Any]:
        """
        Process a user question through the LangGraph StateGraph.

        Returns a dictionary matching the QueryResponse model schema:
          - answer: str
          - confidence: float
          - sources: List[dict]
          - graph_context: List[str]
          - key_entities: List[str]
          - follow_up_suggestions: List[str]
          - evidence_classification: List[dict]
          - contradictions: List[str]
          - canonical_entities: List[dict]
          - sub_questions: List[str]
        """
        print(f"\n================ LANGGRAPH QUERY EXECUTION ================")
        print(f"Question: '{question}' | Clearance Role: '{user_role}'")

        initial_state = {
            "question": question,
            "user_role": user_role,
            "hop_count": 0,
            "raw_entities": [],
            "canonical_entities": [],
            "intents": [],
            "sub_questions": [],
            "vector_results": [],
            "graph_results": [],
            "contradictions": [],
            "validation_report": {},
            "answer": "",
            "sources": [],
            "key_entities": [],
            "follow_up_suggestions": [],
            "confidence": 0.0,
            "formatted_graph_relations": [],
        }

        # Run compiled LangGraph workflow
        final_state = self.workflow.invoke(initial_state)

        val_report = final_state.get("validation_report", {})
        findings = val_report.get("findings", [])

        result = {
            "answer": final_state.get("answer", "I'm sorry, I could not generate an answer based on the retrieved context."),
            "confidence": final_state.get("confidence", 0.0),
            "sources": final_state.get("sources", []),
            "graph_context": final_state.get("formatted_graph_relations", []),
            "key_entities": final_state.get("key_entities", final_state.get("raw_entities", [])),
            "follow_up_suggestions": final_state.get("follow_up_suggestions", []),
            "evidence_classification": findings,
            "contradictions": final_state.get("contradictions", []),
            "canonical_entities": final_state.get("canonical_entities", []),
            "sub_questions": final_state.get("sub_questions", []),
        }

        print(f"================ LANGGRAPH QUERY COMPLETE (Confidence: {result['confidence']}) ================\n")
        return result
