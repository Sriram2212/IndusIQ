"""
Vector Reranker (P2)
====================
Re-scores and reorders vector retrieval results using a combination of:
  1. Cosine similarity (already computed by FAISS → similarity field)
  2. Entity overlap between the query and the chunk text
  3. Evidence-type bonus (DIRECT_FACT chunks are ranked higher)
  4. Recency bonus (if a `date` field exists in metadata)

The reranker returns the top-K results sorted by final score.
"""

import re
from typing import List


# Evidence type score multipliers
EVIDENCE_TYPE_BONUS = {
    "DIRECT_FACT":     0.10,
    "HISTORICAL_FACT": 0.05,
    "INFERRED_FACT":   0.02,
    "RECOMMENDATION":  0.0,
    "HYPOTHESIS":     -0.05,
    "SCHEDULED_ACTION": 0.0,
    "UNKNOWN":          0.0,
}


class VectorReranker:
    """
    Reranks a list of RetrievalResult objects using a composite score.

    Score formula:
        score = (0.70 * similarity)
              + (0.20 * entity_overlap)
              + evidence_type_bonus

    Usage:
        reranker = VectorReranker()
        top_results = reranker.rerank(results, query="...", entities=[...], top_k=3)
    """

    def rerank(
        self,
        results: list,
        query: str,
        entities: List[str] = None,
        top_k: int = 3,
    ) -> list:
        """
        Rerank a list of RetrievalResult objects and return the top-K.

        Args:
            results:  List of RetrievalResult from VectorRetriever.
            query:    The original user question.
            entities: Canonical entity names extracted from the question.
            top_k:    Maximum number of results to return.

        Returns:
            Re-ranked list of RetrievalResult (at most top_k items).
        """
        entities = entities or []

        scored = []
        for result in results:
            score = self._compute_score(result, query, entities)
            scored.append((score, result))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [r for _, r in scored[:top_k]]

    # ─── Internal helpers ──────────────────────────────────────────────────

    def _compute_score(self, result, query: str, entities: List[str]) -> float:
        similarity    = result.metadata.get("similarity", 0.0)
        entity_overlap = self._entity_overlap(result, entities)
        ev_bonus       = self._evidence_bonus(result)

        score = (
            0.70 * similarity
            + 0.20 * entity_overlap
            + ev_bonus
        )
        return round(score, 4)

    @staticmethod
    def _entity_overlap(result, entities: List[str]) -> float:
        """
        Fraction of extracted entities that appear in the chunk text.
        Returns 0.0 if no entities are provided.
        """
        if not entities:
            return 0.0

        text = result.content.lower() if isinstance(result.content, str) else ""
        matched = sum(1 for e in entities if e.lower() in text)
        return matched / len(entities)

    @staticmethod
    def _evidence_bonus(result) -> float:
        """
        Apply a small bonus/penalty based on the evidence_type metadata field.
        """
        ev_type = result.metadata.get("evidence_type", "UNKNOWN")
        return EVIDENCE_TYPE_BONUS.get(ev_type, 0.0)
