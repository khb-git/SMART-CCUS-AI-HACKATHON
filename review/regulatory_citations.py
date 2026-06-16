"""Deterministic regulatory citation mapping for Class VI review outputs."""

from __future__ import annotations


REGULATORY_CITATIONS_BY_PLAN_TYPE = {
    "project_narrative": [
        "40 CFR 146.82 - Required Class VI permit information",
    ],
    "site_geologic_characterization": [
        "40 CFR 146.82 - Required Class VI permit information",
        "40 CFR 146.83 - Minimum criteria for siting",
    ],
    "aor_corrective_action": [
        "40 CFR 146.84 - Area of review and corrective action",
    ],
    "financial_responsibility": [
        "40 CFR 146.85 - Financial responsibility",
    ],
    "well_construction": [
        "40 CFR 146.86 - Injection well construction requirements",
    ],
    "pre_operational_testing": [
        "40 CFR 146.87 - Logging, sampling, and testing prior to injection well operation",
    ],
    "site_operating": [
        "40 CFR 146.88 - Injection well operating requirements",
        "40 CFR 146.89 - Mechanical integrity",
    ],
    "testing_monitoring": [
        "40 CFR 146.90 - Testing and monitoring requirements",
        "40 CFR 146.91 - Reporting requirements",
    ],
    "injection_well_plugging": [
        "40 CFR 146.92 - Injection well plugging",
    ],
    "pisc_site_closure": [
        "40 CFR 146.93 - Post-injection site care and site closure",
    ],
    "emergency_remedial_response": [
        "40 CFR 146.94 - Emergency and remedial response",
    ],
}


def regulatory_citations_for_plan_type(plan_type: str) -> list[str]:
    """Return deterministic regulatory citations for a checklist plan type."""
    return REGULATORY_CITATIONS_BY_PLAN_TYPE.get(str(plan_type or ""), [])


def format_regulatory_citations(plan_type: str) -> str:
    """Return reviewer-facing citation text for a checklist plan type."""
    citations = regulatory_citations_for_plan_type(plan_type)

    if not citations:
        return "Not mapped"

    return "; ".join(citations)