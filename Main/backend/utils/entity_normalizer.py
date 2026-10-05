"""
Entity Normalizer (P1)
======================
Maps raw entity strings extracted from questions and documents to
canonical IDs and typed entities, ensuring consistent representation
across the vector store and knowledge graph.

Canonical ID format: "<type_prefix>:<slug>"
  - Equipment  → "equipment:<slug>"   e.g. "equipment:pump_p101"
  - Component  → "component:<slug>"   e.g. "component:bearing"
  - Person     → "person:<slug>"      e.g. "person:raj"
  - Issue      → "issue:<slug>"       e.g. "issue:bearing_overheating"
  - Process    → "process:<slug>"     e.g. "process:lubrication"
  - Material   → "material:<slug>"    e.g. "material:oil"
  - Location   → "location:<slug>"    e.g. "location:pump_house"
  - Sensor     → "sensor:<slug>"      e.g. "sensor:vibration_sensor_v01"
"""

import re
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────
# Entity Types
# ─────────────────────────────────────────────

ENTITY_TYPES = {
    "EQUIPMENT",
    "COMPONENT",
    "PERSON",
    "ISSUE",
    "PROCESS",
    "MATERIAL",
    "LOCATION",
    "SENSOR",
    "UNKNOWN",
}

# Prefix used in canonical IDs per entity type
TYPE_PREFIX = {
    "EQUIPMENT": "equipment",
    "COMPONENT": "component",
    "PERSON":    "person",
    "ISSUE":     "issue",
    "PROCESS":   "process",
    "MATERIAL":  "material",
    "LOCATION":  "location",
    "SENSOR":    "sensor",
    "UNKNOWN":   "unknown",
}

# ─────────────────────────────────────────────
# Keyword heuristics for type inference
# ─────────────────────────────────────────────

TYPE_KEYWORDS = {
    "EQUIPMENT": [
        "pump", "motor", "compressor", "turbine", "boiler", "valve",
        "blower", "fan", "reactor", "vessel", "gearbox", "conveyor",
        "agitator", "generator",
    ],
    "COMPONENT": [
        "bearing", "seal", "gasket", "impeller", "rotor", "shaft",
        "coupling", "belt", "gear", "blade", "vane", "o-ring",
        "bushing", "liner",
    ],
    "PERSON": [
        "technician", "engineer", "operator", "inspector", "manager",
        "supervisor", "raj", "rajan", "kannan", "kumar",
    ],
    "ISSUE": [
        "overheating", "vibration", "leakage", "failure", "fault",
        "wear", "corrosion", "cavitation", "noise", "crack",
        "contamination", "erosion",
    ],
    "PROCESS": [
        "lubrication", "inspection", "maintenance", "repair",
        "overhaul", "cleaning", "calibration", "balancing",
        "alignment", "flushing", "oil analysis",
    ],
    "MATERIAL": [
        "oil", "grease", "coolant", "lubricant", "solvent",
        "nitrogen", "hydrogen", "methane",
    ],
    "SENSOR": [
        "sensor", "transmitter", "transducer", "probe", "thermocouple",
        "accelerometer", "pressure gauge",
    ],
    "LOCATION": [
        "unit", "plant", "area", "section", "bay", "floor",
        "building", "zone", "field",
    ],
}


@dataclass
class CanonicalEntity:
    """A normalised, typed entity with a stable canonical ID."""
    entity_id:   str          # e.g. "equipment:pump_p101"
    name:        str          # human-readable original name
    type:        str          # one of ENTITY_TYPES
    aliases:     list = field(default_factory=list)


# ─────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────

def _slugify(text: str) -> str:
    """Convert a string to a lowercase URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    return text


def _infer_type(name: str) -> str:
    """
    Infer the entity type from the name using keyword heuristics.
    Returns the best matching type or 'UNKNOWN'.
    """
    lower = name.lower()
    for entity_type, keywords in TYPE_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                return entity_type
    return "UNKNOWN"


def build_canonical_id(name: str, entity_type: Optional[str] = None) -> str:
    """
    Build a canonical ID string from a name and optional type.
    If type is not provided, it is inferred from the name.
    """
    if not entity_type or entity_type not in ENTITY_TYPES:
        entity_type = _infer_type(name)
    prefix = TYPE_PREFIX.get(entity_type, "unknown")
    return f"{prefix}:{_slugify(name)}"


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

class EntityNormalizer:
    """
    Normalises raw entity strings into CanonicalEntity objects.

    Usage:
        normalizer = EntityNormalizer()
        entity = normalizer.normalize("Pump P101")
        # → CanonicalEntity(entity_id="equipment:pump_p101", name="Pump P101", type="EQUIPMENT")
    """

    def __init__(self):
        # In-memory registry: entity_id → CanonicalEntity
        self._registry: dict[str, CanonicalEntity] = {}

    def normalize(
        self,
        name: str,
        entity_type: Optional[str] = None,
    ) -> CanonicalEntity:
        """
        Normalise a single entity name.
        Returns an existing CanonicalEntity if already registered,
        otherwise creates and registers a new one.
        """
        if not entity_type or entity_type not in ENTITY_TYPES:
            entity_type = _infer_type(name)

        entity_id = build_canonical_id(name, entity_type)

        if entity_id in self._registry:
            # Add alias if this is a new surface form
            ce = self._registry[entity_id]
            if name not in ce.aliases and name != ce.name:
                ce.aliases.append(name)
            return ce

        ce = CanonicalEntity(
            entity_id=entity_id,
            name=name,
            type=entity_type,
            aliases=[],
        )
        self._registry[entity_id] = ce
        return ce

    def normalize_list(
        self,
        names: list,
        entity_type: Optional[str] = None,
    ) -> list:
        """Normalise a list of entity name strings."""
        return [self.normalize(n, entity_type) for n in names]

    def get(self, entity_id: str) -> Optional[CanonicalEntity]:
        """Retrieve a registered entity by its canonical ID."""
        return self._registry.get(entity_id)

    def all_entities(self) -> list:
        """Return all registered canonical entities."""
        return list(self._registry.values())
