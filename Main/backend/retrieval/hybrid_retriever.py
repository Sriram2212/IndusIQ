"""
Hybrid Retriever — P1 + P2 Enhanced
=====================================
Combines:
  - Vector semantic search (reranked — P2)
  - Targeted graph path traversal (P1) with path ranking (P2)
  - Entity canonicalization on every retrieved entity (P1)
  - Contradiction detection between the two sources (P1)
"""

from backend.retrieval.vector_retriever import VectorRetriever
from backend.retrieval.graph_retriever import GraphRetriever
from backend.utils.entity_normalizer import EntityNormalizer
from backend.utils.contradiction_detector import ContradictionDetector
from backend.utils.reranker import VectorReranker


class HybridRetriever:
    """
    Combines vector-based semantic search with knowledge-graph
    traversal to provide richer context for answer generation.

    P1 enhancements:
      - Canonical entity IDs on every result.
      - Targeted graph traversal driven by query intent.
      - Contradiction detection between vector and graph evidence.

    P2 enhancements:
      - Vector result reranking using composite score.
      - Graph path ranking (shortest paths first).
    """

    def __init__(self):
        self.vector_retriever = VectorRetriever()
        self.graph_retriever  = GraphRetriever()
        self.normalizer       = EntityNormalizer()
        self.detector         = ContradictionDetector()
        self.reranker         = VectorReranker()

    def retrieve(self, question: str, entities: list, intents: list = None) -> dict:
        """
        Perform hybrid retrieval.

        Args:
            question: The user's natural-language question.
            entities: Raw entity names extracted from the question.
            intents:  Optional list of QueryIntent objects (one per entity)
                      produced by QueryDecomposer.  When supplied, each
                      entity is retrieved using its targeted intent.

        Returns:
            Dictionary with:
              vector_results  – reranked RetrievalResult list
              graph_results   – ranked path RetrievalResult list
              contradictions  – list of detected contradiction strings
              canonical_entities – list of CanonicalEntity objects
        """
        intents = intents or []

        # ── Step 1: Canonicalize entities (P1) ──────────────────────────
        canonical_entities = self.normalizer.normalize_list(entities)
        print(f"\n[SEARCH] Hybrid Retriever — Entities (canonicalized):")
        for ce in canonical_entities:
            print(f"   {ce.name}  ->  {ce.entity_id}  [{ce.type}]")

        # ── Step 2: Vector retrieval + reranking (P2) ────────────────────
        print("\n[SEARCH] Hybrid Retriever -- Vector Search")
        raw_vector_results = self.vector_retriever.retrieve(question)
        vector_results = self.reranker.rerank(
            raw_vector_results,
            query=question,
            entities=entities,
            top_k=3,
        )
        print(f"   Found {len(raw_vector_results)} chunks -> reranked to top {len(vector_results)}")

        # ── Step 3: Targeted graph traversal (P1 + P2) ────────────────────
        print("[SEARCH] Hybrid Retriever -- Graph Traversal (targeted)")
        graph_results = []

        for i, entity in enumerate(entities):
            intent = intents[i] if i < len(intents) else None
            try:
                entity_results = self.graph_retriever.retrieve(entity, intent=intent)
                graph_results.extend(entity_results)
                mode = "targeted" if intent and intent.relation else "broad fallback"
                print(f"   Entity '{entity}' [{mode}] -> {len(entity_results)} relations")
            except Exception as e:
                err = str(e).encode("ascii", "replace").decode("ascii")
                print(f"   [WARNING] Graph lookup failed for '{entity}': {err}")

        print(f"   Total graph results: {len(graph_results)}")

        # ── Step 4: Contradiction detection (P1) ──────────────────────────
        print("[SEARCH] Hybrid Retriever -- Contradiction Detection")
        contradictions = self.detector.detect(vector_results, graph_results)
        if contradictions:
            print(f"   [WARNING] {len(contradictions)} contradiction(s) detected:")
            for c in contradictions:
                print(f"     * {c}")
        else:
            print("   No contradictions detected.")

        return {
            "vector_results":     vector_results,
            "graph_results":      graph_results,
            "contradictions":     contradictions,
            "canonical_entities": canonical_entities,
        }

    # ─────────────────────────────────────────────────────────────
    # Context formatters
    # ─────────────────────────────────────────────────────────────

    def format_vector_context(self, vector_results: list) -> str:
        """Format vector retrieval results into a readable text block for LLM prompt."""
        if not vector_results:
            return "No document context available."

        parts = []
        for i, result in enumerate(vector_results):
            meta = result.metadata

            source_parts = []
            if meta.get("document"):
                source_parts.append(f"document: {meta['document']}")
            if meta.get("page"):
                source_parts.append(f"page: {meta['page']}")
            if meta.get("sheet"):
                source_parts.append(f"sheet: {meta['sheet']}")
            if meta.get("section"):
                source_parts.append(f"section: {meta['section']}")
            if meta.get("similarity") is not None:
                source_parts.append(f"similarity: {meta['similarity']:.2f}")
            if meta.get("evidence_type"):
                source_parts.append(f"evidence: {meta['evidence_type']}")

            source = f" (Source: {', '.join(source_parts)})" if source_parts else ""
            chunk_label = meta.get("chunk_id", i)
            parts.append(f"[Document Chunk {chunk_label}]{source}\n{result.content}")

        return "\n\n".join(parts)

    def format_graph_context(self, graph_results: list) -> str:
        """Format graph retrieval results into a readable text block for LLM prompt."""
        if not graph_results:
            return "No graph context available."

        parts = []
        for i, result in enumerate(graph_results):
            content = result.content
            depth_tag = ""
            if isinstance(content, dict):
                source       = content.get("source", "?")
                relationship = content.get("relationship", "?")
                target       = content.get("target", "?")
                depth        = content.get("depth")
                if depth:
                    depth_tag = f" [depth={depth}]"
                parts.append(
                    f"[Relation {i + 1}]{depth_tag} "
                    f"{source} -[{relationship}]-> {target}"
                )
            else:
                parts.append(f"[Relation {i + 1}] {content}")

        return "\n".join(parts)

