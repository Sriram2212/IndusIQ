"""
Neo4j Live Connection Test
---------------------------
Tests connection to your Neo4j Desktop database and shows all stored nodes,
relationships, and sample triplets currently in the database.

Run:   .venv\Scripts\python neo4j_test.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI      = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Sri_89730")


def run_test():
    from neo4j import GraphDatabase

    print("=" * 60)
    print("        LIVE NEO4J CONNECTION TEST")
    print("=" * 60)
    print(f"  URI      : {NEO4J_URI}")
    print(f"  Username : {NEO4J_USERNAME}")
    print(f"  Password : {'*' * len(NEO4J_PASSWORD)}")
    print("-" * 60)

    # Force UTF-8 output on Windows console
    import sys
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    try:
        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
            connection_timeout=5
        )

        with driver.session() as session:
            # 1. Neo4j version
            try:
                ver_row = session.run(
                    "CALL dbms.components() YIELD name, versions WHERE name='Neo4j Kernel' RETURN versions[0] AS version LIMIT 1"
                ).single()
                version = ver_row["version"] if ver_row else "unknown"
            except Exception:
                version = "unknown"

            # 2. Node & Relationship counts
            node_count = session.run("MATCH (n) RETURN count(n) AS cnt").single()["cnt"]
            rel_count  = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt").single()["cnt"]

            # 3. Labels
            labels = [
                r["label"]
                for r in session.run("CALL db.labels() YIELD label RETURN label ORDER BY label")
            ]

            # 4. Relationship types
            rel_types = [
                r["rel"]
                for r in session.run(
                    "CALL db.relationshipTypes() YIELD relationshipType AS rel RETURN rel ORDER BY rel"
                )
            ]

        print(f"  [OK] Connected to Neo4j   v{version}")
        print(f"  [OK] Total Nodes          : {node_count}")
        print(f"  [OK] Total Relationships  : {rel_count}")
        print(f"  [OK] Node Labels Found    : {labels}")
        print(f"  [OK] Relationship Types   : {rel_types}")
        print()

        # 5. Sample triplets
        print("  SAMPLE GRAPH TRIPLETS (first 20):")
        print("-" * 60)
        with driver.session() as session:
            rows = session.run(
                """
                MATCH (a)-[r]->(b)
                RETURN a.name AS src, labels(a)[0] AS sl,
                       type(r)  AS rel,
                       b.name   AS tgt, labels(b)[0] AS tl
                LIMIT 20
                """
            )
            count = 0
            for i, row in enumerate(rows, 1):
                src  = row["src"]  or "(no name)"
                sl   = row["sl"]   or "?"
                rel  = row["rel"]
                tgt  = row["tgt"]  or "(no name)"
                tl   = row["tl"]   or "?"
                print(f"  {i:>2}. ({src} :{sl})  --[{rel}]-->  ({tgt} :{tl})")
                count += 1
            if count == 0:
                print("  (No relationships found in database yet)")

        # 6. Node label breakdown
        print()
        print("  NODE LABEL BREAKDOWN:")
        print("-" * 60)
        with driver.session() as session:
            for label in labels:
                cnt_row = session.run(
                    f"MATCH (n:`{label}`) RETURN count(n) AS cnt"
                ).single()
                cnt = cnt_row["cnt"] if cnt_row else 0
                bar = "#" * min(cnt, 30)
                print(f"  {label:<20} {cnt:>4} nodes  {bar}")

        driver.close()
        print()
        print("=" * 60)
        print("  [SUCCESS] Connection test passed!")
        print()
        print("  To VIEW this graph visually in Neo4j Desktop:")
        print("  1. Open Neo4j Desktop")
        print("  2. Click Open  next to your 'neo4j' database")
        print("  3. In Neo4j Browser, paste this Cypher query:")
        print()
        print("     MATCH (a)-[r]->(b) RETURN a,r,b LIMIT 100")
        print()
        print("  4. Press Ctrl+Enter to run — you will see the full graph!")
        print()
        print("  Other useful queries:")
        print("     MATCH (n) RETURN n LIMIT 50                   -- all nodes")
        print("     MATCH (n:Equipment) RETURN n                  -- equipment only")
        print("     MATCH (n:Issue) RETURN n                      -- all issues")
        print("     MATCH (n)-[r:HAS_ISSUE]->(i) RETURN n,r,i    -- equipment with issues")
        print("=" * 60)

    except Exception as e:
        print(f"  [FAIL] Could not connect to Neo4j!")
        print(f"  Error: {e}")
        print()
        print("  FIX: Open Neo4j Desktop and click 'Start' on your database")
        print(f"  then re-run: .venv\\Scripts\\python neo4j_test.py")
        print("=" * 60)


if __name__ == "__main__":
    run_test()
