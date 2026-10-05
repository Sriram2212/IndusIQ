"""
RAG Evaluation Benchmark (P2)
===============================
Provides a lightweight benchmark harness for the industrial RAG pipeline.

Usage:
    python -m tests.benchmark_rag

Each test case defines:
  - question
  - expected_answer_keywords   (any of these should appear in the answer)
  - expected_entities          (entities that should appear in key_entities)
  - expected_graph_relations   (strings that should appear in graph_context)
  - expected_source_keywords   (document name fragments in sources)
  - expected_confidence_range  (min, max)

Metrics reported:
  - Retrieval Recall @K
  - Entity Linking Accuracy
  - Graph Path Hit Rate
  - Citation Accuracy
  - Confidence Calibration (MAE vs expected midpoint)
  - Overall score (0–10)
"""

import sys
import os
import json

# Ensure the project root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.agents.query_agent import QueryAgent


# ─────────────────────────────────────────────
# Test Dataset
# ─────────────────────────────────────────────

BENCHMARK_CASES = [
    {
        "id": "TC-001",
        "question": "Why did Pump P101 fail?",
        "expected_answer_keywords": ["bearing", "overheating", "failure", "pump"],
        "expected_entities":        ["Pump P101", "bearing"],
        "expected_graph_relations": ["HAS_ISSUE", "HAS_COMPONENT"],
        "expected_source_keywords": [],
        "expected_confidence_range": (0.60, 0.95),
    },
    {
        "id": "TC-002",
        "question": "Who replaced the bearing on Pump P101?",
        "expected_answer_keywords": ["technician", "raj", "replaced", "bearing"],
        "expected_entities":        ["Pump P101", "bearing"],
        "expected_graph_relations": ["REPLACED", "REPLACED_BY", "HAS_COMPONENT"],
        "expected_source_keywords": [],
        "expected_confidence_range": (0.60, 0.95),
    },
    {
        "id": "TC-003",
        "question": "What is the status of lubrication work?",
        "expected_answer_keywords": ["lubrication", "completed", "oil", "analysis"],
        "expected_entities":        ["Lubrication", "Oil Analysis"],
        "expected_graph_relations": [],
        "expected_source_keywords": [],
        "expected_confidence_range": (0.50, 0.95),
    },
]


# ─────────────────────────────────────────────
# Metric helpers
# ─────────────────────────────────────────────

def check_keywords(text: str, keywords: list) -> float:
    """Fraction of keywords present in text (case-insensitive)."""
    if not keywords:
        return 1.0
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in text_lower)
    return hits / len(keywords)


def check_entity_linking(result_entities: list, expected: list) -> float:
    if not expected:
        return 1.0
    result_lower = [e.lower() for e in result_entities]
    hits = sum(1 for e in expected if e.lower() in result_lower)
    return hits / len(expected)


def check_graph_hits(graph_context: list, expected_rels: list) -> float:
    if not expected_rels:
        return 1.0
    graph_text = " ".join(graph_context).lower()
    hits = sum(1 for rel in expected_rels if rel.lower() in graph_text)
    return hits / len(expected_rels)


def check_citations(sources: list, expected_keywords: list) -> float:
    if not expected_keywords:
        return 1.0
    sources_text = json.dumps(sources).lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in sources_text)
    return hits / len(expected_keywords)


def check_confidence(confidence: float, expected_range: tuple) -> float:
    lo, hi = expected_range
    mid    = (lo + hi) / 2
    mae    = abs(confidence - mid)
    # Score: 1.0 if in range, penalise by MAE otherwise
    if lo <= confidence <= hi:
        return 1.0
    return max(0.0, 1.0 - mae)


# ─────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────

def run_benchmark():
    agent   = QueryAgent()
    results = []

    print("=" * 60)
    print("  Industrial RAG Evaluation Benchmark")
    print("=" * 60)

    total_scores = []

    for case in BENCHMARK_CASES:
        print(f"\n[{case['id']}] {case['question']}")
        print("-" * 50)

        try:
            resp = agent.query(case["question"])
        except Exception as e:
            print(f"  [ERROR] Agent failed: {e}")
            results.append({**case, "error": str(e), "score": 0.0})
            total_scores.append(0.0)
            continue

        answer        = resp.get("answer", "")
        entities      = resp.get("key_entities", [])
        graph_ctx     = resp.get("graph_context", [])
        sources       = resp.get("sources", [])
        confidence    = resp.get("confidence", 0.0)
        contradictions = resp.get("contradictions", [])

        # Per-metric scores
        m_answer    = check_keywords(answer, case["expected_answer_keywords"])
        m_entity    = check_entity_linking(entities, case["expected_entities"])
        m_graph     = check_graph_hits(graph_ctx, case["expected_graph_relations"])
        m_citation  = check_citations(sources, case["expected_source_keywords"])
        m_confidence = check_confidence(confidence, case["expected_confidence_range"])

        # Weighted overall score (0–1)
        overall = round(
            0.30 * m_answer
            + 0.20 * m_entity
            + 0.20 * m_graph
            + 0.15 * m_citation
            + 0.15 * m_confidence,
            3,
        )

        total_scores.append(overall)

        print(f"  Answer keyword hit:   {m_answer:.2f}")
        print(f"  Entity linking:       {m_entity:.2f}")
        print(f"  Graph path hit rate:  {m_graph:.2f}")
        print(f"  Citation accuracy:    {m_citation:.2f}")
        print(f"  Confidence (score):   {m_confidence:.2f}  [actual={confidence}]")
        print(f"  Contradictions found: {len(contradictions)}")
        print(f"  ──── Weighted score:  {overall:.3f}  ({overall*10:.1f}/10) ────")

        results.append({
            "id":                case["id"],
            "question":          case["question"],
            "answer_snippet":    answer[:150],
            "confidence":        confidence,
            "contradictions":    contradictions,
            "metric_answer":     m_answer,
            "metric_entity":     m_entity,
            "metric_graph":      m_graph,
            "metric_citation":   m_citation,
            "metric_confidence": m_confidence,
            "overall_score":     overall,
        })

    final_score = round(sum(total_scores) / len(total_scores) * 10, 2) if total_scores else 0.0

    print("\n" + "=" * 60)
    print(f"  Benchmark Complete — Overall Score: {final_score}/10")
    print("=" * 60)

    return results, final_score


if __name__ == "__main__":
    run_benchmark()
