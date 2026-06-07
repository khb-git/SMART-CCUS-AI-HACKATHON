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
    PARTIAL = "partial"
    MISSING = "missing"
    UNCLEAR = "unclear"


@dataclass
class ReviewFinding:
    """Finding for one checklist item."""

    item_id: str
    label: str
    status: GapStatus
    severity: str
    requirement_level: str
    matched_terms: list[str] = field(default_factory=list)
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


def sentence_like_excerpts(text: str) -> list[str]:
    """Split document text into rough sentence-like excerpts."""
    cleaned = " ".join(str(text or "").split())
    if not cleaned:
        return []

    # Simple, dependency-free splitting.
    pieces = []
    current = []

    for token in cleaned.split():
        current.append(token)
        if token.endswith((".", "?", "!")):
            pieces.append(" ".join(current).strip())
            current = []

    if current:
        pieces.append(" ".join(current).strip())

    return [piece for piece in pieces if len(piece) >= 25]


def find_supporting_excerpts(
    text: str,
    matched_terms: list[str],
    max_excerpts: int = 2,
) -> list[str]:
    """Find short excerpts that contain matched terms."""
    if not matched_terms:
        return []

    excerpts = []
    sentences = sentence_like_excerpts(text)

    for sentence in sentences:
        normalized_sentence = normalize_text(sentence)

        if any(normalize_text(term) in normalized_sentence for term in matched_terms):
            excerpts.append(sentence)

        if len(excerpts) >= max_excerpts:
            break

    return excerpts


def classify_item_status(
    item: ReviewChecklistItem,
    matched_terms: list[str],
) -> GapStatus:
    """Classify one checklist item based on matched expected evidence terms."""
    total_terms = len(item.expected_evidence_terms)

    if total_terms == 0:
        return GapStatus.UNCLEAR

    match_count = len(matched_terms)

    if match_count == 0:
        return GapStatus.MISSING

    match_fraction = match_count / total_terms

    if match_fraction >= 0.5 or match_count >= 3:
        return GapStatus.PRESENT

    return GapStatus.PARTIAL


def build_finding_text(
    item: ReviewChecklistItem,
    status: GapStatus,
    matched_terms: list[str],
) -> str:
    """Create reviewer-facing finding text."""
    if status == GapStatus.PRESENT:
        return (
            f"The document appears to address '{item.label}' based on matched terms: "
            f"{', '.join(matched_terms)}."
        )

    if status == GapStatus.PARTIAL:
        return (
            f"The document partially addresses '{item.label}', but only limited "
            f"supporting terms were found: {', '.join(matched_terms)}."
        )

    if status == GapStatus.MISSING:
        return (
            f"The document does not appear to address '{item.label}' based on the "
            "expected evidence terms in the checklist."
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

    status = classify_item_status(item, matched_terms)

    supporting_excerpts = find_supporting_excerpts(
        document_text,
        matched_terms,
    )

    return ReviewFinding(
        item_id=item.item_id,
        label=item.label,
        status=status,
        severity=item.severity.value,
        requirement_level=item.requirement_level.value,
        matched_terms=matched_terms,
        supporting_excerpts=supporting_excerpts,
        finding=build_finding_text(item, status, matched_terms),
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
        "partial": 0,
        "missing": 0,
        "unclear": 0,
    }

    for finding in findings:
        counts[finding.status.value] += 1

    return (
        "Checklist review complete. "
        f"Present: {counts['present']}; "
        f"Partial: {counts['partial']}; "
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