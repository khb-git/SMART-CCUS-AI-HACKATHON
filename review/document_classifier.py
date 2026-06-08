"""
Rule-based document type classification for uploaded review documents.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DocumentClassification:
    """Classification result for an uploaded review document."""

    document_type: str
    confidence: str
    matched_terms: list[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self):
        """Return JSON-serializable classification data."""
        return {
            "document_type": self.document_type,
            "confidence": self.confidence,
            "matched_terms": self.matched_terms,
            "reason": self.reason,
        }


DOCUMENT_TYPE_RULES = {
    "testing_monitoring": {
        "label": "Testing and Monitoring Plan",
        "high_confidence_terms": [
            "testing and monitoring plan",
            "testing monitoring plan",
            "testing monitoring",
            "continuous recording of injection",
            "injection pressure monitoring",
            "injection rate monitoring",
            "plume and pressure front tracking",
        ],
        "supporting_terms": [
            "wellhead pressure",
            "flow rate",
            "annular pressure",
            "groundwater monitoring",
            "monitoring frequency",
            "scada",
        ],
    },
    "aor_corrective_action": {
        "label": "Area of Review and Corrective Action Plan",
        "high_confidence_terms": [
            "area of review",
            "corrective action plan",
            "aor and corrective action",
            "aor/corrective action",
            "aor ca plan",
            "aor corrective action",
        ],
        "supporting_terms": [
            "corrective action",
            "computational model",
            "pressure front",
            "legacy wells",
            "artificial penetrations",
        ],
    },
    "emergency_remedial_response": {
        "label": "Emergency and Remedial Response Plan",
        "high_confidence_terms": [
            "emergency and remedial response plan",
            "emergency response plan",
            "remedial response plan",
            "err plan",
            "emergency remedial response",
        ],
        "supporting_terms": [
            "emergency response",
            "remedial response",
            "release response",
            "notification",
            "shut-in",
        ],
    },
    "pisc_site_closure": {
        "label": "Post-Injection Site Care and Site Closure Plan",
        "high_confidence_terms": [
            "post-injection site care",
            "post injection site care",
            "site closure plan",
            "pisc and site closure",
            "pisc sc plan",
            "pisc site closure",
        ],
        "supporting_terms": [
            "site closure",
            "post-injection monitoring",
            "pisc period",
            "non-endangerment",
        ],
    },
    "well_construction": {
        "label": "Well Construction Plan",
        "high_confidence_terms": [
            "well construction plan",
            "construction details",
            "well construction details",
        ],
        "supporting_terms": [
            "casing",
            "cement",
            "tubing",
            "packer",
            "well schematic",
            "injection well construction",
        ],
    },
    "financial_responsibility": {
        "label": "Financial Responsibility Demonstration",
        "high_confidence_terms": [
            "financial responsibility",
            "financial responsibility demonstration",
            "fr demonstration",
        ],
        "supporting_terms": [
            "cost estimate",
            "financial instrument",
            "trust fund",
            "letter of credit",
            "surety bond",
        ],
    },
    "project_narrative": {
        "label": "Project Narrative / Application Narrative",
        "high_confidence_terms": [
            "project narrative",
            "application narrative",
            "class vi permit application",
            "permit application narrative",
        ],
        "supporting_terms": [
            "project description",
            "facility information",
            "injection project",
            "applicant",
        ],
    },
    "pre_operational_testing": {
        "label": "Pre-Operational Testing Plan",
        "high_confidence_terms": [
            "pre-operational testing plan",
            "pre operational testing plan",
            "pre-operational testing",
            "pre operational testing",
            "pre-injection testing",
            "pre injection testing",
            "formation testing",
        ],
        "supporting_terms": [
            "mechanical integrity testing",
            "baseline monitoring",
            "logging before injection",
            "formation testing",
            "injectivity test",
            "step-rate test",
            "pressure falloff",
        ],
    },
    "site_operating": {
        "label": "Site Operating Plan",
        "high_confidence_terms": [
            "site operating plan",
            "operating plan",
            "site operations plan",
        ],
        "supporting_terms": [
            "operating parameters",
            "maximum injection pressure",
            "injection rate",
            "alarm setpoints",
            "shutoff systems",
            "shut-off systems",
        ],
    },
    "site_geologic_characterization": {
        "label": "Site Geologic Characterization",
        "high_confidence_terms": [
            "site geologic characterization",
            "geologic characterization",
            "site characterization",
        ],
        "supporting_terms": [
            "injection zone",
            "confining zone",
            "faults",
            "fractures",
            "hydrogeology",
            "usdw",
            "geochemical data",
        ],
    },
    "injection_well_plugging": {
        "label": "Injection Well Plugging Plan",
        "high_confidence_terms": [
            "injection well plugging plan",
            "well plugging plan",
            "plugging plan",
        ],
        "supporting_terms": [
            "plugging methods",
            "cement plugs",
            "plugging depths",
            "pre-plugging conditions",
            "plugging verification",
            "abandonment",
        ],
    },
}


def normalize_text(value: str) -> str:
    """Normalize text for rule matching."""
    return (
        str(value or "")
        .lower()
        .replace("-", " ")
        .replace("_", " ")
        .replace("/", " ")
        .replace("\\", " ")
    )


def collect_document_text(document, max_chars: int = 50000) -> str:
    """Collect filename and extracted chunk text for classification."""
    filename = getattr(document, "original_filename", "") or ""
    text_parts = [filename]

    chunks = getattr(document, "chunks", []) or []

    for chunk in chunks:
        text = getattr(chunk, "text", "") or ""
        if text:
            text_parts.append(text)

        if sum(len(part) for part in text_parts) >= max_chars:
            break

    return "\n".join(text_parts)[:max_chars]


def match_terms(text: str, terms: list[str]) -> list[str]:
    """Return terms found in normalized text."""
    normalized = normalize_text(text)
    return [term for term in terms if normalize_text(term) in normalized]


def score_document_type(text: str, rule: dict) -> tuple[int, list[str], int]:
    """Score one document type rule."""
    high_matches = match_terms(text, rule.get("high_confidence_terms", []))
    supporting_matches = match_terms(text, rule.get("supporting_terms", []))

    # Plan-title/high-confidence matches should dominate generic supporting terms.
    score = len(high_matches) * 10 + len(supporting_matches)

    return score, high_matches + supporting_matches, len(high_matches)


def confidence_from_score(score: int, matched_terms: list[str]) -> str:
    """Convert score to a simple confidence label."""
    if score >= 5 and matched_terms:
        return "high"

    if score >= 2 and matched_terms:
        return "medium"

    if score >= 1 and matched_terms:
        return "low"

    return "unknown"


def classify_review_document(document) -> DocumentClassification:
    """Classify an uploaded temporary review document."""
    text = collect_document_text(document)

    best_type = "unknown"
    best_score = 0
    best_high_match_count = 0
    best_terms: list[str] = []

    for document_type, rule in DOCUMENT_TYPE_RULES.items():
        score, terms, high_match_count = score_document_type(text, rule)

        if (score, high_match_count) > (best_score, best_high_match_count):
            best_type = document_type
            best_score = score
            best_high_match_count = high_match_count
            best_terms = terms

    confidence = confidence_from_score(best_score, best_terms)

    if best_type == "unknown" or confidence == "unknown":
        return DocumentClassification(
            document_type="unknown",
            confidence="unknown",
            matched_terms=[],
            reason="No supported document type rule matched the uploaded document.",
        )

    label = DOCUMENT_TYPE_RULES[best_type]["label"]

    return DocumentClassification(
        document_type=best_type,
        confidence=confidence,
        matched_terms=best_terms,
        reason=f"Matched uploaded document to {label} using rule-based terms.",
    )