from fastapi import APIRouter, Query, Header
from typing import Optional
 
from backend.graph.neo4j_manager import Neo4jManager
from backend.models.graph_models import CreateNodeRequest
from backend.config.settings import (
    NEO4J_URI,
    NEO4J_USERNAME,
    NEO4J_PASSWORD
)
 
router = APIRouter(
    prefix="/graph",
    tags=["Graph"]
)
 
neo4j_manager = Neo4jManager(
    NEO4J_URI,
    NEO4J_USERNAME,
    NEO4J_PASSWORD
)
 
 
@router.get("/data")
def get_graph_data(
    limit: int = Query(100, ge=10, le=300),
    entity: Optional[str] = None,
    document: Optional[str] = None,
    x_user_role: Optional[str] = Header(None)
):
    """
    Fetch real Neo4j nodes and edges for visual Knowledge Graph rendering.
    If 'entity' is supplied, retrieves the multi-hop ego network around that entity.
    If 'document' is supplied, filters nodes belonging to that specific PDF report.
    Filters output based on user role for security/clearance (RBAC).
    """
    role = (x_user_role or "engineer").lower()
    
    # Define allowed Node Types per role
    if role == "operator":
        allowed_types = {"Equipment", "Location", "Sensor"}
    elif role == "technician":
        allowed_types = {"Equipment", "Component", "Issue", "Technician", "Process", "Location"}
    else: # engineer or admin
        allowed_types = {"Equipment", "Component", "Issue", "Technician", "Process", "Material", "Location", "Sensor"}

    try:
        if entity:
            # Multi-hop subgraph around the entity
            nodes_cypher = """
            MATCH path = (a)-[*1..2]-(b)
            WHERE a.name = $entity OR a.id = $entity
            UNWIND nodes(path) AS n
            RETURN DISTINCT
                coalesce(n.name, n.id) AS id,
                coalesce(n.name, n.id) AS label,
                labels(n)[0] AS type,
                properties(n) AS properties
            LIMIT $limit
            """
            edges_cypher = """
            MATCH path = (a)-[r*1..2]-(b)
            WHERE a.name = $entity OR a.id = $entity
            UNWIND relationships(path) AS rel
            RETURN DISTINCT
                coalesce(startNode(rel).name, startNode(rel).id) AS source,
                type(rel) AS label,
                coalesce(endNode(rel).name, endNode(rel).id) AS target
            LIMIT $limit
            """
            nodes_raw = neo4j_manager.run_cypher(nodes_cypher, {"entity": entity, "limit": limit})
            edges_raw = neo4j_manager.run_cypher(edges_cypher, {"entity": entity, "limit": limit})
        elif document:
            # Subgraph filtered to nodes extracted from specific PDF document
            nodes_cypher = """
            MATCH (n)
            WHERE n.source_doc = $document OR $document IN [n.source_doc, n.document, n.source]
            RETURN DISTINCT
                coalesce(n.name, n.id) AS id,
                coalesce(n.name, n.id) AS label,
                labels(n)[0] AS type,
                properties(n) AS properties
            LIMIT $limit
            """
            edges_cypher = """
            MATCH (a)-[r]->(b)
            WHERE (a.source_doc = $document OR $document IN [a.source_doc, a.document, a.source])
              AND (b.source_doc = $document OR $document IN [b.source_doc, b.document, b.source])
            RETURN DISTINCT
                coalesce(a.name, a.id) AS source,
                type(r) AS label,
                coalesce(b.name, b.id) AS target
            LIMIT $limit
            """
            nodes_raw = neo4j_manager.run_cypher(nodes_cypher, {"document": document, "limit": limit})
            edges_raw = neo4j_manager.run_cypher(edges_cypher, {"document": document, "limit": limit * 2})
            # Fallback if properties not yet backfilled
            if not nodes_raw:
                nodes_cypher_fallback = """
                MATCH (n)
                RETURN DISTINCT
                    coalesce(n.name, n.id) AS id,
                    coalesce(n.name, n.id) AS label,
                    labels(n)[0] AS type,
                    properties(n) AS properties
                LIMIT $limit
                """
                nodes_raw = neo4j_manager.run_cypher(nodes_cypher_fallback, {"limit": limit})
                edges_raw = neo4j_manager.run_cypher(
                    "MATCH (a)-[r]->(b) RETURN DISTINCT coalesce(a.name, a.id) AS source, type(r) AS label, coalesce(b.name, b.id) AS target LIMIT $limit",
                    {"limit": limit * 2}
                )
        else:
            # Full graph sample
            nodes_cypher = """
            MATCH (n)
            RETURN DISTINCT
                coalesce(n.name, n.id) AS id,
                coalesce(n.name, n.id) AS label,
                labels(n)[0] AS type,
                properties(n) AS properties
            LIMIT $limit
            """
            edges_cypher = """
            MATCH (a)-[r]->(b)
            RETURN DISTINCT
                coalesce(a.name, a.id) AS source,
                type(r) AS label,
                coalesce(b.name, b.id) AS target
            LIMIT $limit
            """
            nodes_raw = neo4j_manager.run_cypher(nodes_cypher, {"limit": limit})
            edges_raw = neo4j_manager.run_cypher(edges_cypher, {"limit": limit * 2})

        # Deduplicate and ensure clean IDs
        node_ids = set()
        cleaned_nodes = []
        for n in nodes_raw:
            nid = n.get("id")
            ntype = n.get("type") or "Entity"
            if nid and nid not in node_ids and ntype in allowed_types:
                node_ids.add(nid)
                props = n.get("properties") or {}
                # Ensure default source document if not set
                if "source_doc" not in props:
                    props["source_doc"] = document or "transformer_inspection_report.pdf"
                cleaned_nodes.append({
                    "id": nid,
                    "label": n.get("label") or nid,
                    "type": ntype,
                    "properties": props
                })

        cleaned_edges = []
        for e in edges_raw:
            src = e.get("source")
            tgt = e.get("target")
            if src in node_ids and tgt in node_ids:
                cleaned_edges.append({
                    "source": src,
                    "target": tgt,
                    "label": e.get("label") or "RELATED_TO"
                })

        return {
            "nodes": cleaned_nodes,
            "edges": cleaned_edges,
            "count": {
                "nodes": len(cleaned_nodes),
                "edges": len(cleaned_edges)
            },
            "user_role": role,
            "allowed_types": list(allowed_types)
        }
    except Exception as e:
        print(f"[GRAPH ERROR] Error fetching graph data: {e}")
        return {
            "nodes": [],
            "edges": [],
            "count": {"nodes": 0, "edges": 0},
            "error": str(e)
        }


@router.get("/assets")
def get_plant_assets():
    """
    Returns dynamic list of plant equipment discovered from the Neo4j Knowledge Graph.
    If Neo4j is offline or has no equipment, returns an empty list (no static mocks).
    """
    try:
        query = """
        MATCH (e)
        WHERE e:Equipment OR e:Asset OR labels(e)[0] IN ['Equipment', 'Asset']
        RETURN DISTINCT
            coalesce(e.name, e.id) AS name,
            e.id AS id,
            coalesce(e.type, 'Equipment') AS type,
            coalesce(e.status, 'Normal') AS status
        LIMIT 50
        """
        results = neo4j_manager.run_cypher(query)
        assets = []
        for r in results:
            assets.append({
                "name": r.get("name") or r.get("id"),
                "id": r.get("id") or r.get("name"),
                "type": r.get("type") or "Equipment",
                "status": r.get("status") or "Normal"
            })
        return assets
    except Exception as e:
        print(f"[GRAPH ASSETS ERROR] {e}")
        return []


@router.get("/stats")
def get_graph_stats():
    """
    Returns live statistics of the Neo4j Knowledge Graph.
    """
    try:
        schema = neo4j_manager.get_graph_schema()
        node_count = neo4j_manager.run_cypher("MATCH (n) RETURN count(n) AS count")[0]["count"]
        edge_count = neo4j_manager.run_cypher("MATCH ()-[r]->() RETURN count(r) AS count")[0]["count"]
        
        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "labels": list(schema.get("labels", [])),
            "relationships": list(schema.get("relationships", []))
        }
    except Exception as e:
        print(f"Error fetching graph stats: {e}")
        return {
            "node_count": 0,
            "edge_count": 0,
            "labels": [],
            "relationships": [],
            "error": str(e)
        }


@router.post("/node")
def create_node(request: CreateNodeRequest, x_user_role: Optional[str] = Header(None)):
    role = (x_user_role or "engineer").lower()
    if role != "engineer":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403,
            detail="Access Denied: Creating or modifying Knowledge Graph nodes requires Chief Engineer clearance."
        )
    result = neo4j_manager.create_node(
        request.label,
        request.properties
    )
    return {
        "message": "Node created successfully",
        "result": result
    }