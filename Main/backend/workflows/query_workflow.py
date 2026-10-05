"""
LangGraph Query Workflow for Industrial Copilot.
Implements an agentic stateful graph with dynamic routing, corrective graph hops,
evidence validation, answer generation, citation verification, and confidence calibration.
"""

import json
import re
from typing import Any, Dict, List

from langgraph.graph import StateGraph, START, END

from backend.llm.gemini_service import GeminiService
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.utils.entity_normalizer import EntityNormalizer
from backend.utils.query_decomposer import QueryDecomposer, QueryIntent
from backend.utils.contradiction_detector import ContradictionDetector
from backend.prompts.query_prompts import (
    ENTITY_EXTRACTION_FROM_QUERY_PROMPT,
    EVIDENCE_VALIDATION_PROMPT,
    ANSWER_GENERATION_PROMPT,
)
from backend.utils.helpers import safe_json_parse
from backend.workflows.state import QueryWorkflowState


class QueryWorkflowBuilder:
    """
    Builder for compiling the LangGraph Query Agentic Workflow.
    """

    def __init__(self):
        self.llm = GeminiService()
        self.retriever = HybridRetriever()
        self.normalizer = EntityNormalizer()
        self.decomposer = QueryDecomposer()
        self.detector = ContradictionDetector()

    # ─────────────────────────────────────────────────────────────
    # Node 1: Extract Entities & Decompose Query
    # ─────────────────────────────────────────────────────────────
    def extract_and_decompose_node(self, state: QueryWorkflowState) -> Dict[str, Any]:
        question = state.get("question", "")
        print(f"\n[LANGGRAPH:NODE] 1. Extract & Decompose — '{question}'")

        # LLM Entity Extraction with regex fallback
        raw_entities = []
        prompt = ENTITY_EXTRACTION_FROM_QUERY_PROMPT.format(question=question)
        try:
            response = self.llm.generate(prompt)
            data = safe_json_parse(response)
            extracted = data.get("entities", [])
            if extracted:
                raw_entities = extracted
        except Exception as e:
            print(f"   [WARNING] LLM entity extraction failed in graph node: {e}")

        if not raw_entities:
            # Smart Regex fallback for industrial tags, filenames, and equipment
            print("   [INFO] Regex fallback entity extraction activated in LangGraph")
            stopwords = {"summarize", "system", "directive", "user", "synthesize", "exclude", "explain", "findings", "what", "where", "when", "which", "how", "please"}
            files = re.findall(r'[\w\-]+\.(?:pdf|docx|xlsx|csv)', question, re.IGNORECASE)
            tags = re.findall(r'\b[A-Z0-9]{2,}-[\w\-]+|\b(?:Pump|Motor|Gearbox|Valve|Sensor|Feeder)\s+[\w\-]+|\b[A-Z]{1,3}\d{2,4}\b', question, re.IGNORECASE)
            caps = re.findall(r'\b[A-Z][a-zA-Z0-9\-]{2,}\b', question)
            
            seen = set()
            for e in files + tags + caps:
                clean_e = e.strip()
                if clean_e.lower() not in stopwords and clean_e.lower() not in seen:
                    seen.add(clean_e.lower())
                    raw_entities.append(clean_e)

        print(f"   Extracted entities: {raw_entities}")

        # Query decomposition into intents
        try:
            intents = self.decomposer.decompose(question, entities=raw_entities)
        except Exception as e:
            print(f"   [WARNING] Query decomposition failed: {e}")
            intents = [QueryIntent(question=question)]

        sub_questions = [i.question for i in intents]
        print(f"   Decomposed into {len(sub_questions)} sub-question(s): {sub_questions}")

        return {
            "raw_entities": raw_entities,
            "intents": intents,
            "sub_questions": sub_questions,
            "hop_count": state.get("hop_count", 0),
        }

    # ─────────────────────────────────────────────────────────────
    # Node 2: Canonicalize Entities
    # ─────────────────────────────────────────────────────────────
    def canonicalize_entities_node(self, state: QueryWorkflowState) -> Dict[str, Any]:
        raw_entities = state.get("raw_entities", [])
        print(f"\n[LANGGRAPH:NODE] 2. Canonicalize Entities ({len(raw_entities)} items)")
        canonical = self.normalizer.normalize_list(raw_entities)
        canonical_dicts = [
            {"entity_id": ce.entity_id, "name": ce.name, "type": ce.type}
            for ce in canonical
        ]
        for ce in canonical:
            print(f"   {ce.name} -> {ce.entity_id} [{ce.type}]")

        return {"canonical_entities": canonical_dicts}

    # ─────────────────────────────────────────────────────────────
    # Node 3: Hybrid Retrieval
    # ─────────────────────────────────────────────────────────────
    def hybrid_retrieve_node(self, state: QueryWorkflowState) -> Dict[str, Any]:
        question = state.get("question", "")
        raw_entities = state.get("raw_entities", [])
        intents = state.get("intents", [])

        print(f"\n[LANGGRAPH:NODE] 3. Hybrid Retrieve (Vector Rerank + Graph Traversal)")
        retrieval_data = self.retriever.retrieve(
            question,
            raw_entities,
            intents=intents,
        )

        return {
            "vector_results": retrieval_data.get("vector_results", []),
            "graph_results": retrieval_data.get("graph_results", []),
            "contradictions": retrieval_data.get("contradictions", []),
        }

    # ─────────────────────────────────────────────────────────────
    # Node 4: Validate Evidence & Detect Contradictions
    # ─────────────────────────────────────────────────────────────
    def validate_evidence_node(self, state: QueryWorkflowState) -> Dict[str, Any]:
        question = state.get("question", "")
        vector_results = state.get("vector_results", [])
        graph_results = state.get("graph_results", [])
        existing_contradictions = state.get("contradictions", [])

        print(f"\n[LANGGRAPH:NODE] 4. Validate Evidence (Contradiction & Factuality Check)")

        vector_context = self.retriever.format_vector_context(vector_results)
        graph_context = self.retriever.format_graph_context(graph_results)

        # Run contradiction detector across current evidence
        detected_contradictions = self.detector.detect(vector_results, graph_results)
        all_contradictions = list(set(existing_contradictions + detected_contradictions))

        validation_prompt = EVIDENCE_VALIDATION_PROMPT.format(
            question=question,
            vector_context=vector_context,
            graph_context=graph_context,
        )

        try:
            val_response = self.llm.generate(validation_prompt)
            val_response = val_response.replace("```json", "").replace("```", "").strip()
            validation_report = safe_json_parse(val_response)
        except Exception as e:
            print(f"   [WARNING] Evidence validation LLM call failed: {e}")
            validation_report = {"evidence_directness": 0.5, "findings": [], "contradictions": []}

        if all_contradictions:
            curr_c = validation_report.get("contradictions", [])
            validation_report["contradictions"] = list(set(curr_c + all_contradictions))

        return {
            "validation_report": validation_report,
            "contradictions": all_contradictions,
        }

    # ─────────────────────────────────────────────────────────────
    # Conditional Router: Should Expand Graph? (Agentic Corrective Loop)
    # ─────────────────────────────────────────────────────────────
    def eval_evidence_router(self, state: QueryWorkflowState) -> str:
        val_report = state.get("validation_report", {})
        directness = val_report.get("evidence_directness", 0.5)
        graph_results = state.get("graph_results", [])
        raw_entities = state.get("raw_entities", [])
        hop_count = state.get("hop_count", 0)

        # If graph evidence is completely empty or directness is weak (<0.4), and we haven't expanded yet
        if (len(graph_results) == 0 or directness < 0.4) and hop_count < 1 and len(raw_entities) > 0:
            print(f"   [LANGGRAPH:ROUTER] Evidence directness={directness}, graph_results={len(graph_results)} -> Routing to Dynamic Graph Expansion")
            return "expand_graph"

        print(f"   [LANGGRAPH:ROUTER] Evidence satisfactory (directness={directness}) -> Routing to Answer Generation")
        return "generate_answer"

    # ─────────────────────────────────────────────────────────────
    # Node 5: Dynamic Graph Expansion (Corrective Step)
    # ─────────────────────────────────────────────────────────────
    def expand_graph_node(self, state: QueryWorkflowState) -> Dict[str, Any]:
        raw_entities = state.get("raw_entities", [])
        existing_graph_results = list(state.get("graph_results", []))
        hop_count = state.get("hop_count", 0)

        print(f"\n[LANGGRAPH:NODE] 5. Dynamic Graph Expansion (Corrective Hop {hop_count + 1})")

        new_results = []
        for ent in raw_entities:
            try:
                # Use dynamic BFS traversal up to 3 hops without rigid relation constraints
                paths = self.retriever.graph_retriever.graph.ranked_paths(
                    subject=ent,
                    relation=None,
                    object_type=None,
                    max_hops=3,
                    top_k=5,
                )
                if paths:
                    res = self.retriever.graph_retriever._paths_to_results(paths)
                    new_results.extend(res)
            except Exception as e:
                print(f"   [WARNING] Graph expansion failed for '{ent}': {e}")

        combined = existing_graph_results + new_results
        print(f"   Expanded graph results: {len(existing_graph_results)} -> {len(combined)}")

        return {
            "graph_results": combined,
            "hop_count": hop_count + 1,
        }

    # ─────────────────────────────────────────────────────────────
    # Node 6: Generate Answer
    # ─────────────────────────────────────────────────────────────
    def generate_answer_node(self, state: QueryWorkflowState) -> Dict[str, Any]:
        question = state.get("question", "")
        role = (state.get("user_role") or "engineer").lower()
        val_report = state.get("validation_report", {})
        raw_entities = state.get("raw_entities", [])
        vector_results = state.get("vector_results", [])
        graph_results = state.get("graph_results", [])

        print(f"\n[LANGGRAPH:NODE] 6. Generate Cited Answer (User Role: {role})")

        role_directives = {
            "technician": "Synthesize answer with direct, step-by-step troubleshooting, maintenance, and repair instructions. Exclude financial/business talk, focus on physical equipment and tools.",
            "operator": "Focus on safety guidelines, real-time operating conditions, alarm limits, and basic visual sensor statuses. Keep instructions simple and direct.",
            "engineer": "Provide deep technical specs, engineering formulae/theory, design parameters, and schema explanations."
        }
        directive = role_directives.get(role, role_directives["engineer"])
        question_context = f"{question}\n\n[System Directive: Clearance is {role.upper()}. {directive}]"

        generation_prompt = ANSWER_GENERATION_PROMPT.format(
            question=question_context,
            validation_report=json.dumps(val_report, indent=2),
        )

        try:
            llm_response = self.llm.generate(generation_prompt)
            llm_response = llm_response.replace("```json", "").replace("```", "").strip()
            parsed_result = safe_json_parse(llm_response)
        except Exception as e:
            print(f"   [WARNING] Answer generation LLM call failed: {e}")
            vector_context = self.retriever.format_vector_context(vector_results)
            parsed_result = {
                "answer": f"Analysis of indexed documents for '{question}':\n\n{vector_context if vector_context else 'No matching sections found in indexed documents.'}",
                "sources": [{"type": "document", "name": getattr(r, 'source', 'Document'), "detail": "Retrieved vector excerpt"} for r in vector_results],
                "key_entities": raw_entities,
                "follow_up_suggestions": [f"Operational condition of {e}" for e in raw_entities[:2]],
            }

        answer = parsed_result.get("answer", "I'm sorry, I could not generate an answer based on the retrieved context.")
        sources = parsed_result.get("sources", [])
        for src in sources:
            if "name" in src and "document" not in src:
                src["document"] = src["name"]
            elif "document" in src and "name" not in src:
                src["name"] = src["document"]

        key_entities = parsed_result.get("key_entities", raw_entities)
        follow_up = parsed_result.get("follow_up_suggestions", [])

        return {
            "answer": answer,
            "sources": sources,
            "key_entities": key_entities,
            "follow_up_suggestions": follow_up,
        }

    # ─────────────────────────────────────────────────────────────
    # Node 7: Verify Citations & Calibrate Confidence
    # ─────────────────────────────────────────────────────────────
    def verify_and_calibrate_node(self, state: QueryWorkflowState) -> Dict[str, Any]:
        sources = state.get("sources", [])
        vector_results = state.get("vector_results", [])
        graph_results = state.get("graph_results", [])
        val_report = state.get("validation_report", {})
        contradictions = state.get("contradictions", [])
        raw_entities = state.get("raw_entities", [])

        print(f"\n[LANGGRAPH:NODE] 7. Verify Citations & Calibrate Confidence")

        # 1. Citation verification against retrieved documents
        retrieved_docs = {
            r.metadata.get("document", "").lower()
            for r in vector_results
            if hasattr(r, "metadata")
        }
        retrieved_docs.add("knowledge graph")

        for src in sources:
            doc_name = (src.get("document") or src.get("name") or "").lower()
            src_type = src.get("type", "document").lower()
            if src_type == "graph" or doc_name in retrieved_docs:
                src["verified"] = True
            else:
                src["verified"] = False

        # 2. Programmatic confidence calculation
        top_vector_sim = 0.0
        if vector_results:
            top_vector_sim = max([
                r.metadata.get("similarity", 0.0) for r in vector_results
                if hasattr(r, "metadata")
            ] or [0.0])

        directness = val_report.get("evidence_directness", 0.5)
        graph_support = 1.0 if graph_results else 0.0

        entity_match = 0.0
        if raw_entities:
            matched = 0
            top_chunks_text = " ".join([
                r.content.lower() for r in vector_results[:2]
                if hasattr(r, "content") and isinstance(r.content, str)
            ])
            graph_text = " ".join([
                f"{r.content.get('source','')} {r.content.get('target','')}".lower()
                for r in graph_results
                if hasattr(r, "content") and isinstance(r.content, dict)
            ])
            for ent in raw_entities:
                if ent.lower() in top_chunks_text or ent.lower() in graph_text:
                    matched += 1
            entity_match = matched / len(raw_entities)

        raw_confidence = (
            0.40 * top_vector_sim
            + 0.30 * directness
            + 0.20 * graph_support
            + 0.10 * entity_match
        )

        penalty = self.detector.confidence_penalty(contradictions)
        confidence = round(min(0.95, max(0.0, raw_confidence - penalty)), 2)

        # 3. Format graph relations for output
        formatted_graph_relations = []
        for res in graph_results:
            content = res.content if hasattr(res, "content") else res
            if isinstance(content, dict):
                rels = content.get("relationship", "?")
                source = content.get("source", "?")
                target = content.get("target", "?")
                depth = content.get("depth")
                depth_tag = f" [depth={depth}]" if depth else ""
                formatted_graph_relations.append(
                    f"{source} -[{rels}]-> {target}{depth_tag}"
                )

            else:
                formatted_graph_relations.append(str(content))

        return {
            "sources": sources,
            "confidence": confidence,
            "formatted_graph_relations": formatted_graph_relations,
        }


def create_query_workflow():
    """
    Assembles and compiles the Query LangGraph StateGraph.
    """
    builder = QueryWorkflowBuilder()
    workflow = StateGraph(QueryWorkflowState)

    # Register Nodes
    workflow.add_node("extract_and_decompose", builder.extract_and_decompose_node)
    workflow.add_node("canonicalize_entities", builder.canonicalize_entities_node)
    workflow.add_node("hybrid_retrieve", builder.hybrid_retrieve_node)
    workflow.add_node("validate_evidence", builder.validate_evidence_node)
    workflow.add_node("expand_graph", builder.expand_graph_node)
    workflow.add_node("generate_answer", builder.generate_answer_node)
    workflow.add_node("verify_and_calibrate", builder.verify_and_calibrate_node)

    # Build Edges
    workflow.add_edge(START, "extract_and_decompose")
    workflow.add_edge("extract_and_decompose", "canonicalize_entities")
    workflow.add_edge("canonicalize_entities", "hybrid_retrieve")
    workflow.add_edge("hybrid_retrieve", "validate_evidence")

    # Conditional Routing from Validation: expand graph vs generate answer
    workflow.add_conditional_edges(
        "validate_evidence",
        builder.eval_evidence_router,
        {
            "expand_graph": "expand_graph",
            "generate_answer": "generate_answer",
        }
    )

    # Loop back from expansion to validation
    workflow.add_edge("expand_graph", "validate_evidence")

    workflow.add_edge("generate_answer", "verify_and_calibrate")
    workflow.add_edge("verify_and_calibrate", END)

    return workflow.compile()
