"""
Query Decomposer (P2)
======================
Breaks complex multi-hop questions into a list of simpler sub-questions
that can be answered individually and then synthesised.

Example:
    "Who replaced the bearing on Pump P101 and what was the root cause?"
    →
    [
        "Who replaced the bearing on Pump P101?",
        "What was the root cause of the issue with Pump P101?",
    ]

The decomposer also extracts a structured query intent per sub-question:
    {
        "question": "Who replaced the bearing on Pump P101?",
        "subject": "Pump P101",
        "relation": "REPLACED_BY",
        "object_type": "PERSON",
    }

If the question is already simple (single intent), it is returned as-is.
"""

import re
from typing import List, Optional
from dataclasses import dataclass, field


# ─────────────────────────────────────────────
# Relation intent vocabulary
# ─────────────────────────────────────────────

# Maps question cue phrases to a (relation, object_type) pair.
# These MUST match the actual Neo4j schema — see GraphService.SCHEMA.
#
#   Actual relationships: HAS_COMPONENT, HAS_ISSUE, INSPECTED, REPLACED,
#                         PERFORMED, PERFORMED_ON, LOCATED_AT, MONITORS, USES
#   Actual node labels:   Equipment, Component, Technician, Issue, Process,
#                         Material, Location, Sensor
INTENT_MAP = [
    # TECHNICIAN questions  (graph uses "Technician", not "Person")
    (re.compile(r"\bwho\s+(replaced|changed)\b",             re.IGNORECASE), "REPLACED",       "Technician"),
    (re.compile(r"\bwho\s+(performed|did|carried\s+out)\b",  re.IGNORECASE), "PERFORMED",      "Technician"),
    (re.compile(r"\bwho\s+inspected\b",                      re.IGNORECASE), "INSPECTED",      "Technician"),
    (re.compile(r"\bwho\s+is\s+responsible\b",               re.IGNORECASE), "INSPECTED",      "Technician"),

    # CAUSE / ISSUE questions
    (re.compile(r"\bwhy\s+did\b",                            re.IGNORECASE), "HAS_ISSUE",      "Issue"),
    (re.compile(r"\broot\s+cause\b",                         re.IGNORECASE), "HAS_ISSUE",      "Issue"),
    (re.compile(r"\bfailure\s+(mode|reason|cause)\b",        re.IGNORECASE), "HAS_ISSUE",      "Issue"),
    (re.compile(r"\bissue\b",                                re.IGNORECASE), "HAS_ISSUE",      "Issue"),
    (re.compile(r"\bproblem\b",                              re.IGNORECASE), "HAS_ISSUE",      "Issue"),

    # COMPONENT questions
    (re.compile(r"\bwhich\s+component\b",                    re.IGNORECASE), "HAS_COMPONENT",  "Component"),
    (re.compile(r"\bwhat\s+component\b",                     re.IGNORECASE), "HAS_COMPONENT",  "Component"),
    (re.compile(r"\bparts?\s+of\b",                          re.IGNORECASE), "HAS_COMPONENT",  "Component"),

    # STATUS / PROCESS questions
    (re.compile(r"\bstatus\s+of\b",                          re.IGNORECASE), "PERFORMED_ON",   "Process"),
    (re.compile(r"\bprogress\s+of\b",                        re.IGNORECASE), "PERFORMED_ON",   "Process"),
    (re.compile(r"\bmaintenance\b",                          re.IGNORECASE), "PERFORMED_ON",   "Process"),
    (re.compile(r"\blubrication\b",                          re.IGNORECASE), "PERFORMED_ON",   "Process"),

    # RECOMMENDATION / ACTION  (no specific graph rel — use None for dynamic)
    (re.compile(r"\brecommend",                              re.IGNORECASE), None,             "Process"),
    (re.compile(r"\bfollow.?up\b",                           re.IGNORECASE), None,             "Process"),
    (re.compile(r"\bschedul",                                re.IGNORECASE), None,             "Process"),

    # LOCATION
    (re.compile(r"\bwhere\b",                                re.IGNORECASE), "LOCATED_AT",     "Location"),

    # SENSOR / MONITORING
    (re.compile(r"\bmonitor",                                re.IGNORECASE), "MONITORS",       "Sensor"),
    (re.compile(r"\bsensor\b",                               re.IGNORECASE), "MONITORS",       "Sensor"),

    # MATERIAL
    (re.compile(r"\bmaterial\b",                             re.IGNORECASE), "USES",           "Material"),
    (re.compile(r"\boil\b",                                  re.IGNORECASE), "USES",           "Material"),
]


# Multi-hop split indicators
SPLIT_PATTERNS = [
    re.compile(r"\band\b",          re.IGNORECASE),
    re.compile(r"\badditionally\b", re.IGNORECASE),
    re.compile(r"\balso\b",         re.IGNORECASE),
    re.compile(r",\s+"),
]


@dataclass
class QueryIntent:
    """Structured intent extracted from a sub-question."""
    question:    str
    subject:     Optional[str] = None
    relation:    Optional[str] = None
    object_type: Optional[str] = None


def _infer_intent(question: str, entities: list) -> QueryIntent:
    """Match a question to an intent using the INTENT_MAP vocabulary."""
    relation    = None
    object_type = None

    for pattern, rel, obj_type in INTENT_MAP:
        if pattern.search(question):
            relation    = rel
            object_type = obj_type
            break

    # Heuristic: use the first entity mentioned as the subject
    subject = entities[0] if entities else None

    return QueryIntent(
        question=question.strip(),
        subject=subject,
        relation=relation,
        object_type=object_type,
    )


class QueryDecomposer:
    """
    Breaks a complex question into a list of QueryIntent objects.

    Usage:
        decomposer = QueryDecomposer()
        intents = decomposer.decompose(
            question="Who replaced the bearing and what was the root cause?",
            entities=["bearing", "Pump P101"],
        )
    """

    def decompose(self, question: str, entities: list = None) -> List[QueryIntent]:
        """
        Decompose a question into a list of QueryIntent objects.
        Falls back to a single intent if the question cannot be split.
        """
        entities = entities or []
        sub_questions = self._split(question)

        return [_infer_intent(sq, entities) for sq in sub_questions]

    def _split(self, question: str) -> List[str]:
        """
        Try to split a compound question into simpler sub-questions.
        If the question does not appear compound, return it as-is.
        """
        # Quick check: does the question contain a compound indicator?
        compound = any(p.search(question) for p in SPLIT_PATTERNS[:-1])  # skip comma
        if not compound:
            return [question]

        # Split on " and " but only when the second clause starts with a verb/pronoun
        parts = re.split(
            r"\s+and\s+(?=(who|what|when|where|why|how|which)\b)",
            question,
            flags=re.IGNORECASE,
        )

        # Filter out conjunctions that are part of entity names (e.g., "oil and gas")
        cleaned: List[str] = []
        for part in parts:
            part = part.strip()
            if len(part) > 5:  # ignore tiny fragments
                cleaned.append(part)

        return cleaned if len(cleaned) > 1 else [question]
