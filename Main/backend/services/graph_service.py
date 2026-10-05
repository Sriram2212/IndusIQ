from backend.graph.neo4j_manager import Neo4jManager
from backend.config.settings import (
    NEO4J_URI,
    NEO4J_USERNAME,
    NEO4J_PASSWORD
)


class GraphService:

    SCHEMA = {
        "HAS_COMPONENT": {
            "valid_pairs": [
                ("Equipment", "Component"),
                ("Component", "Component")
            ],
            "allow_flip": True
        },
        "HAS_ISSUE": {
            "valid_pairs": [
                ("Equipment", "Issue"),
                ("Component", "Issue")
            ],
            "allow_flip": True
        },
        "INSPECTED": {
            "valid_pairs": [
                ("Technician", "Equipment"),
                ("Technician", "Component")
            ],
            "allow_flip": True
        },
        "REPLACED": {
            "valid_pairs": [
                ("Technician", "Component")
            ],
            "allow_flip": True
        },
        "PERFORMED": {
            "valid_pairs": [
                ("Technician", "Process")
            ],
            "allow_flip": True
        },
        "PERFORMED_ON": {
            "valid_pairs": [
                ("Process", "Equipment"),
                ("Process", "Component")
            ],
            "allow_flip": True
        },
        "LOCATED_AT": {
            "valid_pairs": [
                ("Equipment", "Location"),
                ("Component", "Location"),
                ("Technician", "Location")
            ],
            "allow_flip": True
        },
        "MONITORS": {
            "valid_pairs": [
                ("Sensor", "Equipment"),
                ("Sensor", "Component"),
                ("Sensor", "Issue")
            ],
            "allow_flip": True
        },
        "USES": {
            "valid_pairs": [
                ("Process", "Material"),
                ("Technician", "Material")
            ],
            "allow_flip": True
        }
    }

    def __init__(self):

        self.graph = Neo4jManager(
            NEO4J_URI,
            NEO4J_USERNAME,
            NEO4J_PASSWORD
        )

    def store(self, knowledge, document_name: str = None):

        entities = knowledge.get("entities", [])

        relationships = knowledge.get("relationships", [])

        # Store Nodes
        id_to_label = {}
        for entity in entities:
            props = dict(entity.get("properties", {}))
            if document_name:
                props["source_doc"] = document_name
            eid = props.get("id")
            label = entity.get("label")
            if eid and label:
                id_to_label[eid] = label

            try:
                self.graph.create_node(
                    label=entity["label"],
                    properties=props
                )
            except Exception as e:
                print(f"   [WARNING] Failed to store node '{eid}': {e}")

        # Store Relationships
        for relation in relationships:
            src_id = relation["source_id"]
            rel_type = relation["relationship"]
            tgt_id = relation["target_id"]

            # Get labels
            src_label = id_to_label.get(src_id)
            if not src_label:
                try:
                    src_label = self.graph.get_node_label(src_id)
                except Exception:
                    pass
            
            tgt_label = id_to_label.get(tgt_id)
            if not tgt_label:
                try:
                    tgt_label = self.graph.get_node_label(tgt_id)
                except Exception:
                    pass

            # Validate relationship if schema is defined and labels are known
            if rel_type in self.SCHEMA and src_label and tgt_label:
                rules = self.SCHEMA[rel_type]
                valid_pairs = rules["valid_pairs"]
                
                # Check normal direction
                is_valid = (src_label, tgt_label) in valid_pairs
                
                # Check flipped direction if allowed
                is_flipped = False
                if not is_valid and rules.get("allow_flip"):
                    if (tgt_label, src_label) in valid_pairs:
                        is_valid = True
                        is_flipped = True

                if not is_valid:
                    print(f"   [WARNING] Skipping invalid schema relation: ({src_id}:{src_label}) --[{rel_type}]--> ({tgt_id}:{tgt_label})")
                    continue
                
                if is_flipped:
                    print(f"   [INFO] Standardizing relationship direction (flipped): ({tgt_id}:{tgt_label}) --[{rel_type}]--> ({src_id}:{src_label})")
                    src_id, tgt_id = tgt_id, src_id

            try:
                self.graph.create_relationship(
                    source_id=src_id,
                    relationship=rel_type,
                    target_id=tgt_id
                )
            except Exception as e:
                print(f"   [WARNING] Failed to store relationship {src_id} -> {rel_type} -> {tgt_id}: {e}")