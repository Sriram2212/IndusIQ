"""
Graph Retriever — 3-Tier Dynamic Multi-Hop Search
====================================================
Replaces the original rigid directional retrieval with:

  1. **Tier 1 — Targeted bidirectional**: When intent provides a relation
     and object_type, run a focused bidirectional Cypher traversal.
     Invalid schema labels/relations are auto-dropped.

  2. **Tier 2 — Dynamic BFS**: Schema-agnostic multi-hop breadth-first
     search. Finds ALL paths from the subject up to N hops. Used as
     fallback when targeted search returns nothing.

  3. **Tier 3 — Broad neighbor fallback**: Original get_neighbors() call.
     Used only if both tier 1 and tier 2 fail (e.g. Neo4j errors).
"""

from backend.graph.neo4j_manager import Neo4jManager
from backend.config.settings import (
    NEO4J_URI,
    NEO4J_USERNAME,
    NEO4J_PASSWORD,
)
from backend.retrieval.models import RetrievalResult


class GraphRetriever:

    def __init__(self):
        self.graph = Neo4jManager(
            NEO4J_URI,
            NEO4J_USERNAME,
            NEO4J_PASSWORD,
        )

    # ─────────────────────────────────────────────────────────────
    # Primary entry point
    # ─────────────────────────────────────────────────────────────

    def retrieve(self, entity_name: str, intent=None) -> list:
        """
        Retrieve graph context for a given entity.

        Args:
            entity_name: Raw entity name (used as subject).
            intent:      Optional QueryIntent dataclass with fields:
                           subject, relation, object_type.
                         When provided, targeted+BFS search is used.

        Returns:
            List of RetrievalResult objects.
        """
        subject = entity_name
        relation = None
        object_type = None

        if intent is not None:
            subject     = intent.subject or entity_name
            relation    = intent.relation
            object_type = intent.object_type

        # ── Tier 1+2: ranked_paths handles targeted → BFS fallback ─────
        try:
            paths = self.graph.ranked_paths(
                subject=subject,
                relation=relation,
                object_type=object_type,
                max_hops=2,
                top_k=5,
            )
            if paths:
                return self._paths_to_results(paths)
        except Exception as e:
            err = str(e).encode("ascii", "replace").decode("ascii")
            print(f"   [WARNING] Ranked path search failed: {err}")

        # ── Tier 3: broad neighbor fallback ────────────────────────────
        try:
            graph_results = self.graph.get_neighbors(entity_name)
            return self._neighbors_to_results(graph_results)
        except Exception as e:
            err = str(e).encode("ascii", "replace").decode("ascii")
            print(f"   [WARNING] Graph neighbor lookup failed: {err}")
            return []

    # ─────────────────────────────────────────────────────────────
    # Formatters
    # ─────────────────────────────────────────────────────────────

    def _paths_to_results(self, paths: list) -> list:
        """Convert ranked path records to RetrievalResult objects."""
        output = []
        for path in paths:
            rels = path.get("relationships", [])
            rel_str = " -> ".join(rels) if rels else "RELATED_TO"

            # Include the full node chain if available
            node_chain = path.get("node_chain", [])
            chain_str = " -> ".join(str(n) for n in node_chain) if node_chain else ""


            output.append(
                RetrievalResult(
                    source="graph_targeted",
                    content={
                        "source":        path.get("source", ""),
                        "relationship":  rel_str,
                        "target":        path.get("target", ""),
                        "target_label":  path.get("target_label", ""),
                        "depth":         path.get("depth", 1),
                        "node_chain":    chain_str,
                    },
                    metadata={
                        "evidence_type": "DIRECT_FACT" if path.get("depth", 1) <= 2 else "INFERRED_FACT",
                        "path_depth":    path.get("depth", 1),
                    },
                )
            )
        return output

    def _neighbors_to_results(self, graph_results: list) -> list:
        """Convert broad neighbor records to RetrievalResult objects."""
        output = []
        for item in graph_results:
            output.append(
                RetrievalResult(
                    source="graph",
                    content=item,
                    metadata={"evidence_type": "INFERRED_FACT"},
                )
            )
        return output