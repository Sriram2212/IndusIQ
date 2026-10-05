"""
Contradiction Detector (P1)
===========================
Compares vector-retrieved document chunks against graph-retrieved
relations and flags semantic mismatches.

A contradiction is identified when:
  - A vector chunk explicitly states X, but a graph relation asserts ¬X.
  - Typically detected by checking for negation, opposite predicates, or
    mutually exclusive entity links for the same subject.

Output is a list of contradiction strings that the caller can inject
into the LLM prompt or use to lower the confidence score.
"""

import re
from typing import List


# ─────────────────────────────────────────────
# Simple negation / opposition keyword pairs
# ─────────────────────────────────────────────

NEGATION_PATTERNS = [
    re.compile(r"\bnot\b", re.IGNORECASE),
    re.compile(r"\bno\b", re.IGNORECASE),
    re.compile(r"\bfailed\b", re.IGNORECASE),
    re.compile(r"\bunconfirmed\b", re.IGNORECASE),
    re.compile(r"\binconclusive\b", re.IGNORECASE),
    re.compile(r"\bsuspected\b", re.IGNORECASE),
    re.compile(r"\bhypothesis\b", re.IGNORECASE),
]

# Pairs of semantically opposite words
OPPOSITION_PAIRS = [
    ("completed", "pending"),
    ("completed", "in progress"),
    ("confirmed", "suspected"),
    ("confirmed", "unconfirmed"),
    ("repaired", "failed"),
    ("replaced", "original"),
    ("passed", "failed"),
    ("operational", "shutdown"),
    ("running", "stopped"),
]


def _text_of(result) -> str:
    """Extract plain text from a RetrievalResult regardless of content type."""
    content = result.content
    if isinstance(content, dict):
        parts = [
            str(content.get("source", "")),
            str(content.get("relationship", "")),
            str(content.get("target", "")),
        ]
        return " ".join(parts)
    return str(content)


def _has_negation(text: str) -> bool:
    return any(p.search(text) for p in NEGATION_PATTERNS)


def _find_opposition(text_a: str, text_b: str) -> str | None:
    """
    Return a description if the two texts seem to say opposite things,
    otherwise return None.
    """
    a_lower = text_a.lower()
    b_lower = text_b.lower()
    for word_a, word_b in OPPOSITION_PAIRS:
        a_has = word_a in a_lower
        b_has = word_b in b_lower
        b_has_a = word_a in b_lower
        a_has_b = word_a in b_lower
        if (a_has and b_has) or (b_has_a and a_has_b):
            return f"Vector says '{word_a}' but graph says '{word_b}'"
    return None


class ContradictionDetector:
    """
    Detects contradictions between vector retrieval results and
    graph retrieval results.

    Usage:
        detector = ContradictionDetector()
        conflicts = detector.detect(vector_results, graph_results)
        # → ["Vector chunk mentions 'completed' but graph relation says 'pending'", ...]
    """

    def detect(
        self,
        vector_results: list,
        graph_results: list,
    ) -> List[str]:
        """
        Compare vector and graph results and return a list of
        detected contradictions (as human-readable strings).
        Returns an empty list if no contradictions are found.
        """
        conflicts: List[str] = []

        if not vector_results or not graph_results:
            return conflicts

        vector_texts = [_text_of(r) for r in vector_results]
        graph_texts  = [_text_of(r) for r in graph_results]

        # ── Rule 1: Check for negation in one source absent from the other ──
        vector_combined = " ".join(vector_texts)
        graph_combined  = " ".join(graph_texts)

        vec_negated  = _has_negation(vector_combined)
        graph_negated = _has_negation(graph_combined)

        if vec_negated and not graph_negated:
            conflicts.append(
                "Document context contains negation/uncertainty not reflected "
                "in the knowledge graph."
            )
        elif graph_negated and not vec_negated:
            conflicts.append(
                "Knowledge graph contains negation/uncertainty not reflected "
                "in the document context."
            )

        # ── Rule 2: Semantic opposition between individual chunks and edges ──
        for vt in vector_texts:
            for gt in graph_texts:
                opposition = _find_opposition(vt, gt)
                if opposition:
                    conflicts.append(opposition)

        # De-duplicate
        seen: set[str] = set()
        unique: List[str] = []
        for c in conflicts:
            if c not in seen:
                seen.add(c)
                unique.append(c)

        return unique

    def confidence_penalty(self, conflicts: List[str]) -> float:
        """
        Return a confidence penalty (0.0–0.30) based on the number of
        detected contradictions.
          0 conflicts  → 0.00
          1 conflict   → 0.10
          2 conflicts  → 0.20
          3+ conflicts → 0.30
        """
        n = min(len(conflicts), 3)
        return round(n * 0.10, 2)
