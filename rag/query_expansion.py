"""
Rule-based query expansion for Class VI retrieval.

This module expands natural-language reviewer questions with technical
terms commonly used in Class VI permit applications and EPA guidance.

The original question is still displayed to users. The expanded query is
only used for embedding/retrieval.
"""

from __future__ import annotations


EXPANSION_RULES = {
    "pressure": [
        "injection pressure",
        "wellhead pressure",
        "annulus pressure",
        "annular pressure",
        "downhole pressure",
        "pressure transducer",
        "pressure gauge",
    ],
    "flow": [
        "flow rate",
        "injection rate",
        "mass flow rate",
        "mass flowmeter",
        "Coriolis meter",
        "orifice meter",
        "flow computer",
    ],
    "rate": [
        "flow rate",
        "injection rate",
        "mass flow rate",
        "injection volume",
    ],
    "monitor": [
        "monitoring",
        "continuous recording devices",
        "SCADA",
        "operational parameters",
        "data logger",
        "sampling frequency",
        "recording frequency",
    ],
    "monitoring": [
        "continuous recording devices",
        "testing and monitoring plan",
        "monitoring frequency",
        "operational parameters",
        "40 CFR 146.90",
    ],
    "injection": [
        "injection well",
        "injection tubing",
        "wellhead",
        "injection operations",
        "injection phase",
    ],
    "temperature": [
        "wellhead temperature",
        "CO2 stream temperature",
        "temperature sensor",
        "distributed temperature sensing",
        "DTS",
    ],
    "groundwater": [
        "groundwater monitoring",
        "shallow groundwater wells",
        "water quality monitoring",
        "monitoring wells",
        "sampling",
    ],
    "plume": [
        "CO2 plume",
        "pressure front",
        "plume and pressure front tracking",
        "computational modeling",
        "model calibration",
    ],
    "mechanical integrity": [
        "mechanical integrity test",
        "MIT",
        "annulus pressure",
        "pressure test",
        "40 CFR 146.89",
    ],
}


PHRASE_EXPANSIONS = {
    "flow rate": [
        "injection rate",
        "mass flow rate",
        "mass flowmeter",
        "Coriolis meter",
        "orifice meter",
    ],
    "injection pressure": [
        "wellhead pressure",
        "downhole pressure",
        "annulus pressure",
        "pressure transducer",
    ],
    "testing and monitoring": [
        "testing and monitoring plan",
        "monitoring frequency",
        "continuous recording devices",
        "40 CFR 146.90",
    ],
    "pressure and flow": [
        "injection pressure",
        "flow rate",
        "injection rate",
        "continuous recording devices",
        "mass flowmeter",
    ],
}


def normalize_query_text(query: str) -> str:
    """Normalize query text for matching expansion triggers."""
    return (
        str(query or "")
        .lower()
        .replace("-", " ")
        .replace("_", " ")
        .replace("?", " ")
        .strip()
    )


def unique_terms_preserve_order(terms: list[str]) -> list[str]:
    """Deduplicate terms while preserving first-seen order."""
    seen = set()
    unique = []

    for term in terms:
        normalized = term.lower().strip()
        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        unique.append(term)

    return unique


def get_query_expansion_terms(query: str) -> list[str]:
    """Return expansion terms triggered by the query."""
    normalized = normalize_query_text(query)
    expansions = []

    for phrase, terms in PHRASE_EXPANSIONS.items():
        if phrase in normalized:
            expansions.extend(terms)

    for trigger, terms in EXPANSION_RULES.items():
        if trigger in normalized:
            expansions.extend(terms)

    return unique_terms_preserve_order(expansions)


def expand_query(query: str, enabled: bool = True) -> str:
    """Expand a query with Class VI technical retrieval vocabulary."""
    query = str(query or "").strip()

    if not enabled:
        return query

    expansion_terms = get_query_expansion_terms(query)

    if not expansion_terms:
        return query

    return query + "\n\nExpanded retrieval terms: " + " ".join(expansion_terms)