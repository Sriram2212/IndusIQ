"""
Neo4j Health & Diagnostics Check
==================================
Run this script anytime to verify if Neo4j is online, check credentials,
and inspect real nodes/edges in the database.

Usage:
    python -m tests.check_neo4j
"""

import sys
import os
import socket
from urllib.parse import urlparse

# Ensure project root is in path
current_dir = os.path.dirname(os.path.abspath(__file__))
main_dir = os.path.dirname(current_dir)
if main_dir not in sys.path:
    sys.path.insert(0, main_dir)

from backend.config.settings import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from backend.graph.neo4j_manager import Neo4jManager
from neo4j import GraphDatabase


def parse_host_port(uri: str):
    """Extract host and port from Neo4j URI."""
    try:
        # bolt://localhost:7687 or neo4j://localhost:7687
        cleaned = uri.replace("bolt://", "").replace("neo4j://", "").replace("neo4j+s://", "").replace("bolt+s://", "")
        if ":" in cleaned:
            parts = cleaned.split(":")
            return parts[0], int(parts[1].split("/")[0])
        return cleaned, 7687
    except Exception:
        return "localhost", 7687


def run_diagnostics():
    print("=" * 60)
    print("        NEO4J DATABASE DIAGNOSTICS & HEALTH CHECK        ")
    print("=" * 60)

    print(f"\n[1] Configuration from .env:")
    print(f"    - NEO4J_URI      : {NEO4J_URI}")
    print(f"    - NEO4J_USERNAME : {NEO4J_USERNAME}")
    pwd_masked = "*" * len(NEO4J_PASSWORD) if NEO4J_PASSWORD else "<EMPTY>"
    print(f"    - NEO4J_PASSWORD : {pwd_masked}")

    # Step 1: TCP Socket Check
    host, port = parse_host_port(NEO4J_URI or "bolt://localhost:7687")
    print(f"\n[2] Testing TCP Socket Connection ({host}:{port})...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    try:
        res = s.connect_ex((host, port))
        if res == 0:
            print(f"    [OK] Port {port} is OPEN and accepting TCP connections.")
        else:
            print(f"    [ERROR] Port {port} is CLOSED or unreachable (Error code: {res}).")
            print("    --> Action: Ensure Neo4j Desktop or Neo4j Service is started.")
            return False
    except Exception as e:
        print(f"    [ERROR] TCP Socket error: {e}")
        return False
    finally:
        s.close()

    # Step 2: Driver Authentication & Cypher Query
    print(f"\n[3] Authenticating Driver & Running Cypher Test...")
    try:
        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
            connection_timeout=5.0
        )
        with driver.session() as session:
            test_res = session.run("RETURN 'Connected Successfully' AS msg, datetime() AS ts").single()
            print(f"    [OK] Authentication Successful!")
            print(f"    - Server Response : {test_res['msg']}")
            print(f"    - Server Timestamp: {test_res['ts']}")

            # Step 3: Count Nodes and Relationships
            print(f"\n[4] Inspecting Database Contents:")
            node_count = session.run("MATCH (n) RETURN count(n) AS cnt").single()["cnt"]
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt").single()["cnt"]

            print(f"    - Total Nodes in Database        : {node_count}")
            print(f"    - Total Relationships in Database: {rel_count}")

            if node_count > 0:
                print(f"\n    Sample Node Labels & Names:")
                sample_nodes = session.run("MATCH (n) RETURN coalesce(n.name, n.id, labels(n)[0]) AS name, labels(n)[0] AS lbl LIMIT 5")
                for record in sample_nodes:
                    print(f"      * [{record['lbl']}] {record['name']}")
            else:
                print("    - (Database is currently empty. Upload documents in Document Vault to populate nodes).")

        driver.close()
        print("\n" + "=" * 60)
        print("          STATUS: NEO4J IS FULLY ONLINE & HEALTHY          ")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n    [FAILED] Neo4j Connection Failed.")
        print(f"    - Error Type   : {type(e).__name__}")
        print(f"    - Error Message: {e}")
        print("\n    Troubleshooting Steps:")
        if "Auth" in type(e).__name__ or "unauthorized" in str(e).lower():
            print("    1. Authentication Failed: The password in your .env does not match your Neo4j DBMS password.")
            print("       --> Open Neo4j Desktop, click on your database, click '...', choose 'Reset password', and set it to match NEO4J_PASSWORD in .env.")
        elif "ServiceUnavailable" in type(e).__name__:
            print("    1. Neo4j is stopped or restarting. Open Neo4j Desktop and click the 'Start' button.")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = run_diagnostics()
    sys.exit(0 if success else 1)
