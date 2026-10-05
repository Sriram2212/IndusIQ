import time
from neo4j import GraphDatabase


class Neo4jManager:
    _is_online = None
    _last_check = 0
    _check_interval = 15.0

    def __init__(self, uri, username, password):
        self.driver = GraphDatabase.driver(
            uri,
            auth=(username, password),
            connection_timeout=5.0,
            connection_acquisition_timeout=5.0,
        )

    def is_online(self) -> bool:
        now = time.time()
        if self._is_online is not None and (now - self._last_check) < self._check_interval:
            return self._is_online

        try:
            with self.driver.session(database="neo4j") as session:
                result = session.run("RETURN 1 AS test")
                result.single()
            self._is_online = True
        except Exception:
            self._is_online = False

        self._last_check = now
        return self._is_online

    def close(self):
        self.driver.close()

    def test_connection(self):
        if not self.is_online():
            return "Neo4j Offline"
        with self.driver.session(database="neo4j") as session:
            result = session.run(
                "RETURN 'Neo4j Connected Successfully!' AS message"
            )
            return result.single()["message"]

    def create_node(self, label: str, properties: dict):
        if not self.is_online():
            return None
        query = f"""
        MERGE (n:{label} {{id:$id}})
        SET n += $properties
        RETURN n
        """

        with self.driver.session(database="neo4j") as session:
            result = session.run(
                query,
                id=properties["id"],
                properties=properties
            )
            return result.single()

    def create_relationship(
        self,
        source_id,
        relationship,
        target_id
    ):
        if not self.is_online():
            return None
        query = f"""
        MATCH (a {{id:$source}})
        MATCH (b {{id:$target}})
        MERGE (a)-[r:{relationship}]->(b)
        RETURN r
        """

        with self.driver.session(database="neo4j") as session:
            result = session.run(
                query,
                source=source_id,
                target=target_id
            )
            return result.single()

    def get_neighbors(self, entity_id):
        if not self.is_online():
            return []
        query = """
        MATCH (a {id:$id})-[r]-(b)
        RETURN
            a.name AS source,
            type(r) AS relationship,
            b.name AS target
        """

        with self.driver.session(database="neo4j") as session:
            result = session.run(
                query,
                id=entity_id
            )

            return [record.data() for record in result]

    def get_node_label(self, entity_id):
        if not self.is_online():
            return None
        query = "MATCH (n {id: $id}) RETURN labels(n)[0] AS label"
        with self.driver.session(database="neo4j") as session:
            result = session.run(query, id=entity_id)
            record = result.single()
            return record["label"] if record else None

    def run_cypher(self, query: str, params: dict = None):
        """
        Execute an arbitrary read-only Cypher query and return all records
        as a list of dicts.
        """
        if not self.is_online():
            return []
        params = params or {}
        with self.driver.session(database="neo4j") as session:
            result = session.run(query, **params)
            return [record.data() for record in result]

    # ─────────────────────────────────────────────────────────────
    # Schema introspection (cached)
    # ─────────────────────────────────────────────────────────────

    _schema_cache: dict | None = None

    def get_graph_schema(self) -> dict:
        """
        Introspect the live Neo4j database and return:
          {
              "labels":        {"Equipment", "Component", "Technician", ...},
              "relationships": {"HAS_COMPONENT", "REPLACED", ...},
          }
        Results are cached for the lifetime of this manager instance.
        """
        if self._schema_cache is not None:
            return self._schema_cache

        labels = set()
        rels   = set()
        try:
            with self.driver.session(database="neo4j") as session:
                # Node labels
                result = session.run("CALL db.labels()")
                for record in result:
                    labels.add(record[0])
                # Relationship types
                result = session.run("CALL db.relationshipTypes()")
                for record in result:
                    rels.add(record[0])
        except Exception as e:
            print(f"   [WARNING] Schema introspection failed: {e}")

        self._schema_cache = {"labels": labels, "relationships": rels}
        print(f"   [SCHEMA] Labels: {labels}")
        print(f"   [SCHEMA] Relationships: {rels}")
        return self._schema_cache

    def is_valid_relation(self, relation: str) -> bool:
        """Check if a relationship type actually exists in the graph."""
        schema = self.get_graph_schema()
        return relation in schema["relationships"]

    def is_valid_label(self, label: str) -> bool:
        """Check if a node label actually exists in the graph."""
        schema = self.get_graph_schema()
        return label in schema["labels"]

    # ─────────────────────────────────────────────────────────────
    # Tier 1: Targeted bidirectional path search
    # ─────────────────────────────────────────────────────────────

    def search_path_targeted(
        self,
        subject: str,
        relation: str | None = None,
        object_type: str | None = None,
        max_hops: int = 2,
    ) -> list:
        """
        Bidirectional targeted path search.

        Unlike the old search_path() which only followed outgoing edges,
        this uses `-[r]-` (both directions) so it can find paths like:

            Pump P101 -[HAS_COMPONENT]-> Bearing <-[REPLACED]- Technician

        If `relation` or `object_type` don't exist in the live schema,
        they are silently dropped (the query becomes less constrained
        rather than returning zero results).
        """
        # Validate against live schema — drop invalid constraints
        if relation and not self.is_valid_relation(relation):
            print(f"   [SCHEMA] Relation '{relation}' not in graph — dropping filter")
            relation = None
        if object_type and not self.is_valid_label(object_type):
            print(f"   [SCHEMA] Label '{object_type}' not in graph — dropping filter")
            object_type = None

        rel_clause   = f":{relation}" if relation else ""
        label_clause = f":{object_type}" if object_type else ""
        depth        = f"1..{max_hops}" if max_hops > 1 else "1"

        # Bidirectional traversal  (note: -[r]- not -[r]->)
        query = f"""
        MATCH path = (a)-[r{rel_clause}*{depth}]-(b{label_clause})
        WHERE (a.name = $subject OR a.id = $subject)
          AND a <> b
        RETURN
            a.name  AS source,
            [x IN relationships(path) | type(x)] AS relationships,
            [x IN nodes(path) | coalesce(x.name, x.id)] AS node_chain,
            b.name  AS target,
            labels(b)[0] AS target_label,
            length(path) AS depth
        ORDER BY depth ASC
        LIMIT 20
        """
        with self.driver.session(database="neo4j") as session:
            result = session.run(query, subject=subject)
            return [record.data() for record in result]

    # ─────────────────────────────────────────────────────────────
    # Tier 2: Dynamic schema-agnostic multi-hop BFS
    # ─────────────────────────────────────────────────────────────

    def search_path_dynamic(
        self,
        subject: str,
        max_hops: int = 3,
    ) -> list:
        """
        Schema-agnostic multi-hop BFS.

        No relationship type or label constraints — just find ALL paths
        reachable from `subject` up to `max_hops`, sorted by length.

        This is the "catch-all" when the targeted search returns nothing.
        """
        if not self.is_online():
            return []
        depth = f"1..{max_hops}"

        query = f"""
        MATCH path = (a)-[*{depth}]-(b)
        WHERE (a.name = $subject OR a.id = $subject)
          AND a <> b
        RETURN
            a.name  AS source,
            [x IN relationships(path) | type(x)] AS relationships,
            [x IN nodes(path) | coalesce(x.name, x.id)] AS node_chain,
            b.name  AS target,
            labels(b)[0] AS target_label,
            length(path) AS depth
        ORDER BY depth ASC
        LIMIT 30
        """
        with self.driver.session(database="neo4j") as session:
            result = session.run(query, subject=subject)
            return [record.data() for record in result]

    # ─────────────────────────────────────────────────────────────
    # Ranked paths — deduplicates and returns top-K
    # ─────────────────────────────────────────────────────────────

    def ranked_paths(
        self,
        subject: str,
        relation: str | None = None,
        object_type: str | None = None,
        max_hops: int = 2,
        top_k: int = 5,
    ) -> list:
        """
        3-tier ranked retrieval:
          1. Targeted bidirectional search (if intent provided)
          2. Dynamic BFS fallback (if targeted returns nothing)
          3. Caller can still fall back to get_neighbors()

        Returns at most `top_k` paths, deduplicated by target node.
        """
        if not self.is_online():
            return []
        paths = []

        # Tier 1: targeted bidirectional
        if relation or object_type:
            paths = self.search_path_targeted(
                subject=subject,
                relation=relation,
                object_type=object_type,
                max_hops=max_hops,
            )
            if paths:
                print(f"   [GRAPH] Tier 1 (targeted) found {len(paths)} paths")

        # Tier 2: dynamic BFS fallback
        if not paths:
            paths = self.search_path_dynamic(
                subject=subject,
                max_hops=max_hops + 1,  # allow one extra hop for BFS
            )
            print(f"   [GRAPH] Tier 2 (dynamic BFS) found {len(paths)} paths")

        # Deduplicate by target, prefer shorter paths
        seen_targets: set[str] = set()
        ranked = []
        for p in paths:
            target = p.get("target", "")
            if target and target not in seen_targets:
                seen_targets.add(target)
                ranked.append(p)
            if len(ranked) >= top_k:
                break

        return ranked
