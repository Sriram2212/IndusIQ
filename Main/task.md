## P0 ✅ Completed

- [x] Ingest source & page metadata
- [x] Graph schema validation and flipping
- [x] Programmatic calibrated confidence scores
- [x] Two-step evidence validation and fusion

---

## P1 ✅ Done

- [x] 1. Entity canonicalization → `backend/utils/entity_normalizer.py`
- [x] 2. Targeted graph traversal → `neo4j_manager.py` + `graph_retriever.py`
- [x] 3. Contradiction detection → `backend/utils/contradiction_detector.py`
- [x] 4. Evidence type classification → `RetrievalResult` metadata + prompts
- [x] 5. Better chunk metadata → `vector_service.py` + `vector_retriever.py`
- [x] 6. Wire everything into `query_agent.py`

---

## P2 ✅ Done

- [x] 7. Query decomposition → `backend/utils/query_decomposer.py`
- [x] 8. Vector reranking → `backend/utils/reranker.py`
- [x] 9. Graph path ranking → `neo4j_manager.ranked_paths()` + `graph_retriever.py`
- [x] 10. Answer citation verification → `query_agent._verify_citations()`
- [x] 11. Benchmark harness → `tests/benchmark_rag.py`
