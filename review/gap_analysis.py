"""
Rule-based document gap analysis.

This module checks a temporarily ingested review document against a review
checklist and identifies which required/recommended items appear present,
partial, missing, or unclear.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from review.types import ReviewChecklist, ReviewChecklistItem


class GapStatus(str, Enum):
    """Status for one checklist review item."""

    PRESENT = "present"
    PARTIAL = "evidence_found"
    MISSING = "missing"
    UNCLEAR = "unclear"

ITEM_ANCHOR_TERMS = {
    "injection_pressure_monitoring": [
        "injection pressure",
        "wellhead pressure",
        "downhole pressure",
        "pressure transducer",
        "pressure gauge",
    ],
    "injection_rate_monitoring": [
        "injection rate",
        "flow rate",
        "mass flow rate",
        "mass flowmeter",
        "coriolis meter",
        "orifice meter",
    ],
    "injection_volume_monitoring": [
        "injection volume",
        "injected volume",
        "cumulative volume",
        "daily volume",
    ],
    "annular_pressure_monitoring": [
        "annular pressure",
        "annulus pressure",
        "annulus fluid",
    ],
    "monitoring_frequency": [
        "continuous",
        "frequency",
        "recorded hourly",
        "monthly",
        "annual",
    ],
    "scada_or_data_recording": [
        "scada",
        "continuous recording devices",
        "electronically submit",
        "graphs",
        "daily values",
        "monitoring results",
        "records",
        "tabulation",
    ],
}


@dataclass
class ReviewFinding:
    """Finding for one checklist item."""

    item_id: str
    label: str
    status: GapStatus
    severity: str
    requirement_level: str
    matched_terms: list[str] = field(default_factory=list)
    matched_evidence_groups: dict[str, list[str]] = field(default_factory=dict)
    matched_evidence_group_names: list[str] = field(default_factory=list)
    supporting_excerpts: list[str] = field(default_factory=list)
    finding: str = ""
    recommended_fix: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable finding data."""
        return {
            "item_id": self.item_id,
            "label": self.label,
            "status": self.status.value,
            "severity": self.severity,
            "requirement_level": self.requirement_level,
            "matched_terms": self.matched_terms,
            "supporting_excerpts": self.supporting_excerpts,
            "finding": self.finding,
            "recommended_fix": self.recommended_fix,
            "matched_evidence_groups": self.matched_evidence_groups,
            "matched_evidence_group_names": self.matched_evidence_group_names,
        }


@dataclass
class GapAnalysisReport:
    """Complete review report for one uploaded document."""

    document_name: str
    plan_type: str
    checklist_id: str
    overall_status: str
    summary: str
    findings: list[ReviewFinding]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable report data."""
        return {
            "document_name": self.document_name,
            "plan_type": self.plan_type,
            "checklist_id": self.checklist_id,
            "overall_status": self.overall_status,
            "summary": self.summary,
            "findings": [finding.to_dict() for finding in self.findings],
        }


def normalize_text(value: str) -> str:
    """Normalize text for matching."""
    return " ".join(
        str(value or "")
        .lower()
        .replace("-", " ")
        .replace("_", " ")
        .replace("/", " ")
        .split()
    )

def clean_excerpt_text(value: str, max_length: int = 450) -> str:
    """Clean and shorten supporting excerpts for reviewer-facing output."""
    text = " ".join(str(value or "").split())

    # Repeated section-context prefixes are useful for retrieval but noisy in reports.
    text = text.replace("Section context:", "")

    while "  " in text:
        text = text.replace("  ", " ")

    text = text.strip()

    if len(text) <= max_length:
        return text

    shortened = text[:max_length].rsplit(" ", 1)[0].strip()
    return f"{shortened}..."

def collect_document_text(document) -> str:
    """Collect all temporary review document text."""
    chunks = getattr(document, "chunks", []) or []
    return "\n\n".join(getattr(chunk, "text", "") or "" for chunk in chunks)


def find_matching_terms(text: str, terms: list[str]) -> list[str]:
    """Find checklist expected evidence terms in document text."""
    normalized = normalize_text(text)
    matched = []

    for term in terms:
        normalized_term = normalize_text(term)
        if normalized_term and normalized_term in normalized:
            matched.append(term)

    return matched

def find_matching_evidence_groups(
    text: str,
    evidence_groups: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Return matched evidence terms grouped by evidence category."""
    return {
        group_name: find_matching_terms(text, terms)
        for group_name, terms in evidence_groups.items()
    }


def matched_evidence_group_names(
    matched_groups: dict[str, list[str]],
) -> list[str]:
    """Return evidence group names with at least one matched term."""
    return sorted(
        group_name
        for group_name, matched_terms in matched_groups.items()
        if matched_terms
    )


def flatten_matched_evidence_groups(
    matched_groups: dict[str, list[str]],
) -> list[str]:
    """Flatten matched evidence group terms while preserving readable labels."""
    flattened = []

    for group_name, matched_terms in matched_groups.items():
        for term in matched_terms:
            flattened.append(f"{group_name}: {term}")

    return flattened

def strong_match_count(matched_terms: list[str], item: ReviewChecklistItem) -> int:
    """Count stronger matches for a checklist item.

    Multi-word terms are usually more meaningful than broad one-word terms.
    """
    strong_terms = []

    for term in matched_terms:
        normalized = normalize_text(term)

        if " " in normalized:
            strong_terms.append(term)
            continue

        if normalized in {
            "scada",
            "calibration",
            "continuous",
            "coriolis",
            "orifice",
        }:
            strong_terms.append(term)

    return len(strong_terms)

def sentence_like_excerpts(text: str) -> list[str]:
    """Split document text into rough sentence-like excerpts."""
    cleaned = " ".join(str(text or "").split())
    if not cleaned:
        return []

    # Split on sentence punctuation, but also on repeated section context markers.
    cleaned = cleaned.replace("Section context:", ". Section context:")

    pieces = []
    current = []

    for token in cleaned.split():
        current.append(token)

        if token.endswith((".", "?", "!")) or len(" ".join(current)) > 700:
            pieces.append(" ".join(current).strip())
            current = []

    if current:
        pieces.append(" ".join(current).strip())

    return [clean_excerpt_text(piece) for piece in pieces if len(piece) >= 25]

def table_like_excerpts(text: str) -> list[str]:
    """Return table-aware excerpts from table row text."""
    excerpts = []

    for line in str(text or "").splitlines():
        cleaned = clean_excerpt_text(line)

        if not cleaned:
            continue

        if cleaned.lower().startswith(("table evidence", "table row:")):
            excerpts.append(cleaned)

    return excerpts

def find_supporting_excerpts(
    text: str,
    matched_terms: list[str],
    max_excerpts: int = 2,
    item: ReviewChecklistItem | None = None,
) -> list[str]:
    """Find short excerpts that contain matched terms, preferring item-specific anchors."""
    if not matched_terms:
        return []

    sentences = table_like_excerpts(text) + sentence_like_excerpts(text)
    scored_excerpts = []

    anchor_terms = []
    if item is not None:
        anchor_terms = ITEM_ANCHOR_TERMS.get(item.item_id, [])

    for sentence in sentences:
        normalized_sentence = normalize_text(sentence)

        terms_in_sentence = [
            term
            for term in matched_terms
            if normalize_text(term) in normalized_sentence
        ]

        if not terms_in_sentence:
            continue

        anchors_in_sentence = [
            term
            for term in anchor_terms
            if normalize_text(term) in normalized_sentence
        ]

        # If anchors are defined for this item, avoid excerpts that only match
        # broad terms such as "continuous" without the item-specific concept.
        if anchor_terms and not anchors_in_sentence:
            continue

        score = len(terms_in_sentence) + 2 * len(anchors_in_sentence)

        scored_excerpts.append(
            (
                score,
                clean_excerpt_text(sentence),
            )
        )

    scored_excerpts.sort(key=lambda item_score: item_score[0], reverse=True)

    excerpts = []
    seen = set()

    for _, excerpt in scored_excerpts:
        if excerpt in seen:
            continue

        excerpts.append(excerpt)
        seen.add(excerpt)

        if len(excerpts) >= max_excerpts:
            break

    return excerpts


def classify_item_status(
    item: ReviewChecklistItem,
    matched_terms: list[str],
    matched_groups: dict[str, list[str]] | None = None,
) -> GapStatus:
    """Classify one checklist item based on matched expected evidence."""
    matched_groups = matched_groups or {}
    evidence_group_names = matched_evidence_group_names(matched_groups)

    if item.evidence_groups:
        total_groups = len(item.evidence_groups)
        matched_group_count = len(evidence_group_names)

        if matched_group_count == 0:
            return GapStatus.MISSING

        # If the item defines structured evidence groups, group coverage is more
        # meaningful than raw flat term count. This helps reduce unnecessary
        # "Evidence found" statuses when the right categories are present.
        if matched_group_count == total_groups:
            return GapStatus.PRESENT

        if total_groups >= 3 and matched_group_count >= total_groups - 1:
            return GapStatus.PRESENT

        return GapStatus.PARTIAL

    total_terms = len(item.expected_evidence_terms)

    if total_terms == 0:
        return GapStatus.UNCLEAR

    match_count = len(matched_terms)

    if match_count == 0:
        return GapStatus.MISSING

    strong_count = strong_match_count(matched_terms, item)
    match_fraction = match_count / total_terms

    # Present should require either several strong matches or broad coverage.
    if strong_count >= 3:
        return GapStatus.PRESENT

    if match_fraction >= 0.6 and strong_count >= 2:
        return GapStatus.PRESENT

    return GapStatus.PARTIAL


def build_finding_text(
    item: ReviewChecklistItem,
    status: GapStatus,
    matched_terms: list[str],
    matched_group_names: list[str] | None = None,
) -> str:
    """Create reviewer-facing finding text."""
    matched_group_names = matched_group_names or []

    if matched_group_names:
        evidence_summary = (
            "matched evidence groups: "
            f"{', '.join(matched_group_names)}"
        )
    else:
        evidence_summary = (
            "matched terms: "
            f"{', '.join(matched_terms)}"
        )

    if status == GapStatus.PRESENT:
        return (
            f"The document appears to address '{item.label}' based on "
            f"{evidence_summary}."
        )

    if status == GapStatus.PARTIAL:
        return (
            f"Evidence was found for '{item.label}', but reviewer confirmation is "
            f"recommended because only limited supporting evidence was found: "
            f"{evidence_summary}."
        )

    if status == GapStatus.MISSING:
        return (
            f"The document does not appear to address '{item.label}' based on the "
            "expected evidence terms or evidence groups in the checklist."
        )

    return (
        f"The document could not be clearly evaluated for '{item.label}' because "
        "the checklist item does not have enough expected evidence terms."
    )


def analyze_checklist_item(
    document_text: str,
    item: ReviewChecklistItem,
) -> ReviewFinding:
    """Analyze one checklist item against document text."""
    matched_terms = find_matching_terms(
        document_text,
        item.expected_evidence_terms,
    )

    matched_groups = find_matching_evidence_groups(
        document_text,
        item.evidence_groups,
    )

    matched_group_names = matched_evidence_group_names(matched_groups)

    grouped_matched_terms = flatten_matched_evidence_groups(matched_groups)

    combined_matched_terms = matched_terms + [
        term
        for term in grouped_matched_terms
        if term not in matched_terms
    ]

    status = classify_item_status(
        item,
        matched_terms,
        matched_groups=matched_groups,
    )

    supporting_excerpts = find_supporting_excerpts(
        document_text,
        combined_matched_terms,
        item=item,
    )

    return ReviewFinding(
        item_id=item.item_id,
        label=item.label,
        status=status,
        severity=item.severity.value,
        requirement_level=item.requirement_level.value,
        matched_terms=matched_terms,
        matched_evidence_groups=matched_groups,
        matched_evidence_group_names=matched_group_names,
        supporting_excerpts=supporting_excerpts,
        finding=build_finding_text(
            item,
            status,
            matched_terms,
            matched_group_names=matched_group_names,
        ),
        recommended_fix=item.recommended_fix,
    )


def determine_overall_status(findings: list[ReviewFinding]) -> str:
    """Determine overall readiness status from findings."""
    critical_missing = [
        finding
        for finding in findings
        if finding.severity == "critical" and finding.status == GapStatus.MISSING
    ]
    required_missing = [
        finding
        for finding in findings
        if finding.requirement_level == "required"
        and finding.status in {GapStatus.MISSING, GapStatus.UNCLEAR}
    ]
    partial_items = [
        finding
        for finding in findings
        if finding.status == GapStatus.PARTIAL
    ]

    if critical_missing:
        return "needs_revision"

    if required_missing:
        return "incomplete"

    if partial_items:
        return "mostly_complete"

    return "review_ready"


def build_summary(findings: list[ReviewFinding]) -> str:
    """Build a concise report summary."""
    counts = {
        "present": 0,
        "evidence_found": 0,
        "missing": 0,
        "unclear": 0,
    }

    for finding in findings:
        counts[finding.status.value] += 1

    return (
        "Checklist review complete. "
        f"Present: {counts['present']}; "
        f"Evidence found: {counts['evidence_found']}; "
        f"Missing: {counts['missing']}; "
        f"Unclear: {counts['unclear']}."
    )


def analyze_document_against_checklist(
    document,
    checklist: ReviewChecklist,
) -> GapAnalysisReport:
    """Run gap analysis for a temporary review document against a checklist."""
    document_text = collect_document_text(document)

    findings = [
        analyze_checklist_item(document_text, item)
        for item in checklist.items
    ]

    return GapAnalysisReport(
        document_name=getattr(document, "original_filename", "uploaded_document"),
        plan_type=checklist.plan_type,
        checklist_id=checklist.checklist_id,
        overall_status=determine_overall_status(findings),
        summary=build_summary(findings),
        findings=findings,
    )