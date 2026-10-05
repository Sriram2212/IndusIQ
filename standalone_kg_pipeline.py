"""
Standalone Knowledge Graph Pipeline
===================================
Features:
1. Connects to Neo4j (Local Neo4j, Neo4j Desktop, Docker, or Neo4j AuraDB Cloud).
2. Parses any PDF document (or uses sample data).
3. Uses Google Gemini LLM to extract structured Entities and Relationships.
4. Stores the Knowledge Graph directly into Neo4j using Cypher MERGE queries.
5. Queries and visualizes the extracted graph triplets in the console.
6. Saves extracted graph to 'extracted_kg.json' for local inspection.
"""

import os
import sys
import json
import re
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables (.env)
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Sri_89730")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ---------------------------------------------------------------------
# 1. Neo4j Manager
# ---------------------------------------------------------------------
class SimpleNeo4jClient:
    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.connected = False
        self._init_driver()

    def _init_driver(self):
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                connection_timeout=5.0
            )
            # Verify connectivity
            with self.driver.session() as session:
                res = session.run("RETURN 1 AS test")
                res.single()
            self.connected = True
            print(f"[SUCCESS] Connected to Neo4j at: {self.uri}")
        except Exception as e:
            self.connected = False
            print(f"[WARNING] Could not connect to Neo4j at {self.uri}.")
            print(f"          Reason: {e}")

    def store_knowledge_graph(self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]]):
        if not self.connected or not self.driver:
            print("[INFO] Neo4j is offline. Skipping database write. Data is saved locally in JSON.")
            return

        with self.driver.session() as session:
            # 1. Create Nodes
            for entity in entities:
                label = entity.get("label", "Entity")
                # Sanitize label to alphanumeric only
                safe_label = re.sub(r'[^a-zA-Z0-9_]', '', label) or "Entity"
                props = entity.get("properties", {})
                entity_id = props.get("id") or entity.get("id") or props.get("name", "Unknown")
                props["id"] = entity_id
                props["name"] = props.get("name", entity_id)

                query = f"""
                MERGE (n:{safe_label} {{id: $id}})
                SET n += $props
                RETURN n
                """
                session.run(query, id=entity_id, props=props)

            # 2. Create Relationships
            for rel in relationships:
                src = rel.get("source_id")
                tgt = rel.get("target_id")
                rel_type = rel.get("relationship", "RELATED_TO")
                safe_rel_type = re.sub(r'[^a-zA-Z0-9_]', '_', rel_type.upper()) or "RELATED_TO"

                if not src or not tgt:
                    continue

                query = f"""
                MATCH (a {{id: $source_id}})
                MATCH (b {{id: $target_id}})
                MERGE (a)-[r:{safe_rel_type}]->(b)
                RETURN r
                """
                session.run(query, source_id=src, target_id=tgt)

        print(f"[OK] Stored {len(entities)} nodes and {len(relationships)} relationships into Neo4j!")

    def fetch_graph_summary(self, limit: int = 50) -> List[Dict[str, str]]:
        if not self.connected or not self.driver:
            return []

        with self.driver.session() as session:
            query = f"""
            MATCH (a)-[r]->(b)
            RETURN a.name AS source, labels(a)[0] AS source_label, 
                   type(r) AS relationship, 
                   b.name AS target, labels(b)[0] AS target_label
            LIMIT {limit}
            """
            result = session.run(query)
            records = []
            for rec in result:
                records.append({
                    "source": f"{rec['source']} ({rec['source_label']})",
                    "relationship": rec["relationship"],
                    "target": f"{rec['target']} ({rec['target_label']})"
                })
            return records

    def close(self):
        if self.driver:
            self.driver.close()


# ---------------------------------------------------------------------
# 2. PDF Parser
# ---------------------------------------------------------------------
def extract_text_from_pdf(pdf_path: str) -> str:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    print(f"[INFO] Reading PDF file: {pdf_path}")
    extracted_text = []
    
    # Try PyMuPDF (fitz)
    try:
        import fitz
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                extracted_text.append(f"--- PAGE {page_num + 1} ---\n{text}")
        doc.close()
    except Exception as e:
        print(f"[WARN] PyMuPDF failed ({e}), trying fallback reader...")
        # Fallback to pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    extracted_text.append(f"--- PAGE {page_num + 1} ---\n{text}")
        except Exception as e2:
            raise RuntimeError(f"Failed to extract PDF text: {e2}")

    full_text = "\n\n".join(extracted_text)
    print(f"[OK] Extracted {len(extracted_text)} pages ({len(full_text)} characters).")
    return full_text


# ---------------------------------------------------------------------
# 3. Knowledge Graph Extractor using Gemini
# ---------------------------------------------------------------------
def extract_kg_from_text(text: str, api_key: str) -> Dict[str, Any]:
    from google import genai

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
You are an expert Knowledge Graph Extraction system.
Extract all key entities and relationships from the text below into structured JSON.

ENTITY LABELS:
- Equipment, Component, Technician, Sensor, Issue, Material, Process, Location, Action, Parameter

RELATIONSHIP TYPES (UPPERCASE):
- HAS_COMPONENT, HAS_ISSUE, INSPECTED_BY, LOCATED_AT, CONNECTED_TO, MONITORS, REPLACED, USES, OPERATED_BY, CAUSED_BY

RULES:
1. Return ONLY valid JSON (no markdown formatting, no code backticks).
2. Every entity MUST have "label" and "properties" with "id" and "name".
3. Every relationship MUST have "source_id", "relationship", and "target_id".

OUTPUT JSON FORMAT:
{{
  "entities": [
    {{
      "label": "Equipment",
      "properties": {{
        "id": "Hydraulic Pump P-102",
        "name": "Hydraulic Pump P-102"
      }}
    }},
    {{
      "label": "Issue",
      "properties": {{
        "id": "Seal Leakage",
        "name": "Seal Leakage"
      }}
    }}
  ],
  "relationships": [
    {{
      "source_id": "Hydraulic Pump P-102",
      "relationship": "HAS_ISSUE",
      "target_id": "Seal Leakage"
    }}
  ]
}}

DOCUMENT TEXT:
{text}
"""

    models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-lite-latest"]
    response_text = ""
    for model in models_to_try:
        try:
            print(f"[INFO] Requesting Knowledge Graph extraction via {model}...")
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            response_text = response.text
            break
        except Exception as e:
            print(f"[WARN] Model {model} failed: {e}. Trying next model...")

    if not response_text:
        raise RuntimeError("Failed to get response from Gemini API.")

    # Clean JSON output
    cleaned_json = response_text.strip()
    if cleaned_json.startswith("```json"):
        cleaned_json = cleaned_json[7:]
    if cleaned_json.startswith("```"):
        cleaned_json = cleaned_json[3:]
    if cleaned_json.endswith("```"):
        cleaned_json = cleaned_json[:-3]
    cleaned_json = cleaned_json.strip()

    try:
        data = json.loads(cleaned_json)
        return {
            "entities": data.get("entities", []),
            "relationships": data.get("relationships", [])
        }
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON response: {e}")
        print(f"Raw response:\n{response_text}")
        return {"entities": [], "relationships": []}


# ---------------------------------------------------------------------
# 4. Main Workflow Runner
# ---------------------------------------------------------------------
def run_pipeline(pdf_path: Optional[str] = None):
    print("=" * 65)
    print("      PDF TO NEO4J KNOWLEDGE GRAPH PIPELINE")
    print("=" * 65)

    # 1. Resolve PDF file
    if not pdf_path:
        if len(sys.argv) > 1:
            pdf_path = sys.argv[1]
        else:
            default_samples = [
                "sample_data/sample.pdf",
                "main/sample_data/uploads/sample.pdf"
            ]
            for sample in default_samples:
                if os.path.exists(sample):
                    pdf_path = sample
                    break

    if not pdf_path or not os.path.exists(pdf_path):
        print("[ERROR] No valid PDF file provided or found.")
        print("Usage: python standalone_kg_pipeline.py <path_to_pdf>")
        return

    print(f"[1/4] Target PDF: {pdf_path}")

    # 2. Extract Text from PDF
    doc_text = extract_text_from_pdf(pdf_path)

    # 3. Extract Knowledge Graph via Gemini
    print("\n[2/4] Extracting Entities and Relationships using Gemini LLM...")
    if not GEMINI_API_KEY:
        print("[ERROR] GEMINI_API_KEY is not set in .env file.")
        return

    kg_data = extract_kg_from_text(doc_text, GEMINI_API_KEY)
    entities = kg_data.get("entities", [])
    relationships = kg_data.get("relationships", [])

    print(f"\n[OK] Extracted {len(entities)} Entities and {len(relationships)} Relationships!")

    # Save to local JSON file
    output_json = "extracted_kg.json"
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(kg_data, f, indent=2)
    print(f"[INFO] Saved graph data locally to: {os.path.abspath(output_json)}")

    # Print summary of extracted entities
    print("\n" + "-" * 50)
    print(" EXTRACTED KNOWLEDGE GRAPH PREVIEW")
    print("-" * 50)
    print("ENTITIES:")
    for idx, e in enumerate(entities[:8], 1):
        name = e.get("properties", {}).get("name") or e.get("id")
        label = e.get("label", "Entity")
        print(f"  {idx}. [{label}] {name}")
    if len(entities) > 8:
        print(f"  ... and {len(entities) - 8} more entities")

    print("\nRELATIONSHIPS (TRIPLETS):")
    for idx, r in enumerate(relationships[:10], 1):
        src = r.get("source_id")
        rel = r.get("relationship")
        tgt = r.get("target_id")
        print(f"  {idx}. ({src}) --[{rel}]--> ({tgt})")
    if len(relationships) > 10:
        print(f"  ... and {len(relationships) - 10} more relationships")

    # 4. Connect to Neo4j & Store
    print("\n[3/4] Connecting to Neo4j...")
    neo4j_client = SimpleNeo4jClient(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

    if neo4j_client.connected:
        print("\n[4/4] Writing Knowledge Graph into Neo4j database...")
        neo4j_client.store_knowledge_graph(entities, relationships)

        # Verify by querying back
        print("\n--- Verifying Neo4j Database Contents ---")
        stored_triplets = neo4j_client.fetch_graph_summary(limit=15)
        for t in stored_triplets:
            print(f"  ({t['source']}) -[:{t['relationship']}]-> ({t['target']})")
    else:
        print("\n[TROUBLESHOOTING NEO4J OFFLINE]")
        print("Your Neo4j instance is currently not reachable at: " + NEO4J_URI)
        print("To fix this, check:")
        print("  1. If using Neo4j Desktop: Open the app and click 'Start' on your database.")
        print("  2. If using Neo4j AuraDB (Cloud): Update NEO4J_URI in .env to:")
        print("     NEO4J_URI=neo4j+s://<your-aura-instance-id>.databases.neo4j.io")
        print("  3. If using Docker: Start it with:")
        print("     docker run -d -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/Sri_89730 neo4j:latest")

    neo4j_client.close()
    print("\n" + "=" * 65)
    print(" Pipeline completed successfully!")
    print("=" * 65)


if __name__ == "__main__":
    run_pipeline()
