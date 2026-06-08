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
        "pressure monitoring",
        "pressure recording",
    ],
    "annular": [
        "annular pressure",
        "annulus pressure",
        "annulus fluid pressure",
        "annular fluid pressure",
        "tubing-casing annulus",
        "casing annulus",
        "annulus monitoring",
        "annular pressure monitoring",
        "annulus pressure monitoring",
        "external mechanical integrity",
        "pressure in the annulus",
    ],
    "annulus": [
        "annular pressure",
        "annulus pressure",
        "annulus fluid pressure",
        "annular fluid pressure",
        "tubing-casing annulus",
        "casing annulus",
        "annulus monitoring",
        "annular pressure monitoring",
        "annulus pressure monitoring",
        "external mechanical integrity",
        "pressure in the annulus",
    ],
    "flow": [
        "flow rate",
        "injection rate",
        "mass flow rate",
        "mass flowmeter",
        "Coriolis meter",
        "orifice meter",
        "flow computer",
        "injection volume",
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
        "monitoring network",
        "monitoring plan",
    ],
    "monitoring": [
        "continuous recording devices",
        "testing and monitoring plan",
        "monitoring frequency",
        "operational parameters",
        "monitoring network",
        "subsurface monitoring",
        "40 CFR 146.90",
    ],
    "injection": [
        "injection well",
        "injection tubing",
        "wellhead",
        "injection operations",
        "injection phase",
        "injection rate",
        "injection pressure",
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
        "USDW",
    ],
    "plume": [
        "CO2 plume",
        "carbon dioxide plume",
        "plume tracking",
        "plume monitoring",
        "pressure front",
        "pressure-front tracking",
        "plume and pressure front tracking",
        "computational modeling",
        "model calibration",
        "pressure buildup",
        "area of review",
        "AoR",
        "reservoir pressure",
        "subsurface monitoring",
        "monitoring network",
        "seismic monitoring",
        "groundwater monitoring",
    ],
    "front": [
        "pressure front",
        "pressure-front tracking",
        "plume and pressure front tracking",
        "pressure buildup",
        "reservoir pressure",
        "computational modeling",
        "area of review",
        "AoR",
    ],
    "pisc": [
        "post-injection site care",
        "post injection site care",
        "PISC",
        "site closure",
        "post-injection monitoring",
        "post injection monitoring",
        "non-endangerment demonstration",
        "alternative PISC timeframe",
        "site closure plan",
        "PISC period",
        "plume stabilization",
        "pressure stabilization",
    ],
    "post-injection": [
        "post-injection site care",
        "post injection site care",
        "PISC",
        "site closure",
        "post-injection monitoring",
        "non-endangerment demonstration",
        "site closure plan",
        "PISC period",
        "plume stabilization",
        "pressure stabilization",
    ],
    "closure": [
        "site closure",
        "site closure plan",
        "post-injection site care",
        "PISC",
        "non-endangerment demonstration",
        "closure report",
        "plugging",
        "decommissioning",
    ],
    "financial": [
        "financial responsibility",
        "financial assurance",
        "cost estimate",
        "cost estimates",
        "closure cost",
        "PISC cost",
        "corrective action cost",
        "plugging cost",
        "emergency response cost",
        "letter of credit",
        "surety bond",
        "trust fund",
        "insurance",
        "financial instrument",
        "coverage amount",
    ],
    "responsibility": [
        "financial responsibility",
        "financial assurance",
        "cost estimate",
        "cost estimates",
        "financial instrument",
        "coverage amount",
        "letter of credit",
        "surety bond",
        "trust fund",
        "insurance",
    ],
    "cost": [
        "cost estimate",
        "cost estimates",
        "closure cost",
        "PISC cost",
        "corrective action cost",
        "plugging cost",
        "emergency response cost",
        "financial assurance",
        "coverage amount",
    ],
    "construction": [
        "well construction plan",
        "well construction",
        "casing program",
        "surface casing",
        "long-string casing",
        "cementing program",
        "cement bond log",
        "tubing",
        "packer",
        "injection tubing",
        "well schematic",
        "wellbore construction",
        "construction details",
        "materials compatibility",
    ],
    "casing": [
        "casing program",
        "surface casing",
        "long-string casing",
        "casing depth",
        "casing diameter",
        "casing grade",
        "cementing program",
    ],
    "cement": [
        "cementing program",
        "cement",
        "cement bond log",
        "top of cement",
        "cement plug",
        "cement verification",
    ],
    "mechanical integrity": [
        "mechanical integrity test",
        "MIT",
        "annulus pressure",
        "pressure test",
        "external mechanical integrity",
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
        "flow computer",
    ],
    "injection pressure": [
        "wellhead pressure",
        "downhole pressure",
        "annulus pressure",
        "annular pressure",
        "pressure transducer",
        "pressure gauge",
    ],
    "annular pressure": [
        "annulus pressure",
        "annulus fluid pressure",
        "annular fluid pressure",
        "tubing-casing annulus",
        "casing annulus",
        "annulus monitoring",
        "annular pressure monitoring",
        "external mechanical integrity",
    ],
    "annulus pressure": [
        "annular pressure",
        "annulus fluid pressure",
        "annular fluid pressure",
        "tubing-casing annulus",
        "casing annulus",
        "annulus monitoring",
        "annulus pressure monitoring",
        "external mechanical integrity",
    ],
    "testing and monitoring": [
        "testing and monitoring plan",
        "monitoring frequency",
        "continuous recording devices",
        "operational parameters",
        "40 CFR 146.90",
    ],
    "pressure and flow": [
        "injection pressure",
        "flow rate",
        "injection rate",
        "continuous recording devices",
        "mass flowmeter",
        "Coriolis meter",
        "orifice meter",
    ],
    "plume and pressure front": [
        "CO2 plume",
        "carbon dioxide plume",
        "plume tracking",
        "plume monitoring",
        "pressure front",
        "pressure-front tracking",
        "pressure buildup",
        "computational modeling",
        "model calibration",
        "area of review",
        "AoR",
        "reservoir pressure",
        "subsurface monitoring",
    ],
    "pressure front": [
        "pressure-front tracking",
        "plume and pressure front tracking",
        "pressure buildup",
        "reservoir pressure",
        "computational modeling",
        "area of review",
        "AoR",
    ],
    "post-injection site care": [
        "post injection site care",
        "PISC",
        "site closure",
        "post-injection monitoring",
        "post injection monitoring",
        "non-endangerment demonstration",
        "alternative PISC timeframe",
        "site closure plan",
        "PISC period",
        "plume stabilization",
        "pressure stabilization",
    ],
    "site closure": [
        "post-injection site care",
        "PISC",
        "site closure plan",
        "non-endangerment demonstration",
        "closure report",
        "plume stabilization",
        "pressure stabilization",
    ],
    "financial responsibility": [
        "financial assurance",
        "cost estimate",
        "cost estimates",
        "closure cost",
        "PISC cost",
        "corrective action cost",
        "plugging cost",
        "emergency response cost",
        "letter of credit",
        "surety bond",
        "trust fund",
        "insurance",
        "financial instrument",
        "coverage amount",
    ],
    "financial assurance": [
        "financial responsibility",
        "cost estimate",
        "cost estimates",
        "financial instrument",
        "coverage amount",
        "letter of credit",
        "surety bond",
        "trust fund",
        "insurance",
    ],
    "well construction": [
        "well construction plan",
        "casing program",
        "surface casing",
        "long-string casing",
        "cementing program",
        "cement bond log",
        "tubing",
        "packer",
        "injection tubing",
        "well schematic",
        "wellbore construction",
        "construction details",
        "materials compatibility",
    ],
    "well construction plan": [
        "casing program",
        "surface casing",
        "long-string casing",
        "cementing program",
        "cement bond log",
        "tubing",
        "packer",
        "injection tubing",
        "well schematic",
        "wellbore construction",
        "construction details",
        "materials compatibility",
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
        normalized_phrase = normalize_query_text(phrase)
        if normalized_phrase in normalized:
            expansions.extend(terms)

    for trigger, terms in EXPANSION_RULES.items():
        normalized_trigger = normalize_query_text(trigger)
        if normalized_trigger in normalized:
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