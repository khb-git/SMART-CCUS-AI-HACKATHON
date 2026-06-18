"""Data model for populated Class VI completeness checklist rows.

This module defines the structured output model for the future checklist
population workflow.

Architecture:
    Backend decides.
    Retriever finds.
    Reviewer confirms.
    LLM explains.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from review.types import ReviewChecklist, ReviewChecklistItem

class ChecklistPopulationStatus(str, Enum):
    """Reviewer-facing status for one populated checklist row."""

    PRESENT = "present"
    MISSING = "missing"
    UNCLEAR = "unclear"
    REDACTED = "redacted"
    NEEDS_REVIEWER_ATTENTION = "needs_reviewer_attention"
    NOT_APPLICABLE_OPTIONAL = "not_applicable_optional"


class ChecklistSectionStatus(str, Enum):
    """Reviewer-facing status for one checklist section."""

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"
    GRAY = "gray"


class ReviewerConfirmationStatus(str, Enum):
    """Reviewer confirmation state for a populated checklist row."""

    PENDING_REVIEW = "pending_review"
    CONFIRMED = "confirmed"
    REVISED = "revised"
    REJECTED = "rejected"


@dataclass
class PopulatedChecklistEvidence:
    """Evidence used to populate one checklist row."""

    file_name: str = ""
    page_number: int | None = None
    excerpt: str = ""
    source_label: str = ""
    confidence: str = "Low"

    def to_dict(self) -> dict:
        """Return JSON-serializable evidence data."""
        return {
            "file_name": self.file_name,
            "page_number": self.page_number,
            "excerpt": self.excerpt,
            "source_label": self.source_label,
            "confidence": self.confidence,
        }


@dataclass
class PopulatedChecklistRow:
    """One populated row from the Class VI completeness checklist."""

    section_title: str
    checklist_item: str
    citation: str = ""
    status: ChecklistPopulationStatus = ChecklistPopulationStatus.MISSING
    gsdt_module_folder: str = ""
    file_name: str = ""
    page_number: int | None = None
    evidence_excerpt: str = ""
    system_notes: str = ""
    reviewer_notes: str = ""
    reviewer_confirmation: ReviewerConfirmationStatus = (
        ReviewerConfirmationStatus.PENDING_REVIEW
    )
    confidence: str = "Low"
    evidence: list[PopulatedChecklistEvidence] = field(default_factory=list)
    is_optional: bool = False

    def to_dict(self) -> dict:
        """Return JSON-serializable row data."""
        return {
            "section_title": self.section_title,
            "checklist_item": self.checklist_item,
            "citation": self.citation,
            "status": self.status.value,
            "gsdt_module_folder": self.gsdt_module_folder,
            "file_name": self.file_name,
            "page_number": self.page_number,
            "evidence_excerpt": self.evidence_excerpt,
            "system_notes": self.system_notes,
            "reviewer_notes": self.reviewer_notes,
            "reviewer_confirmation": self.reviewer_confirmation.value,
            "confidence": self.confidence,
            "evidence": [item.to_dict() for item in self.evidence],
            "is_optional": self.is_optional,
        }


@dataclass
class ChecklistSectionSummary:
    """Summary for one Class VI completeness checklist section."""

    section_title: str
    status: ChecklistSectionStatus
    total_rows: int = 0
    present_rows: int = 0
    missing_rows: int = 0
    unclear_rows: int = 0
    redacted_rows: int = 0
    needs_reviewer_attention_rows: int = 0
    optional_not_applicable_rows: int = 0

    def to_dict(self) -> dict:
        """Return JSON-serializable section summary data."""
        return {
            "section_title": self.section_title,
            "status": self.status.value,
            "total_rows": self.total_rows,
            "present_rows": self.present_rows,
            "missing_rows": self.missing_rows,
            "unclear_rows": self.unclear_rows,
            "redacted_rows": self.redacted_rows,
            "needs_reviewer_attention_rows": (
                self.needs_reviewer_attention_rows
            ),
            "optional_not_applicable_rows": (
                self.optional_not_applicable_rows
            ),
        }


@dataclass
class PopulatedChecklist:
    """Complete populated checklist output for one package review."""

    package_name: str
    rows: list[PopulatedChecklistRow] = field(default_factory=list)
    section_summaries: list[ChecklistSectionSummary] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Return JSON-serializable populated checklist data."""
        return {
            "package_name": self.package_name,
            "rows": [row.to_dict() for row in self.rows],
            "section_summaries": [
                summary.to_dict()
                for summary in self.section_summaries
            ],
        }


def status_counts_for_rows(
    rows: list[PopulatedChecklistRow],
) -> dict[ChecklistPopulationStatus, int]:
    """Count checklist row statuses."""
    counts = {
        status: 0
        for status in ChecklistPopulationStatus
    }

    for row in rows:
        counts[row.status] += 1

    return counts


def determine_section_status(
    rows: list[PopulatedChecklistRow],
) -> ChecklistSectionStatus:
    """Determine section status from populated checklist rows."""
    if not rows:
        return ChecklistSectionStatus.GRAY

    required_rows = [
        row
        for row in rows
        if not row.is_optional
    ]

    if not required_rows:
        return ChecklistSectionStatus.GRAY

    counts = status_counts_for_rows(required_rows)

    if counts[ChecklistPopulationStatus.MISSING] > 0:
        return ChecklistSectionStatus.RED

    if (
        counts[ChecklistPopulationStatus.UNCLEAR] > 0
        or counts[ChecklistPopulationStatus.REDACTED] > 0
        or counts[ChecklistPopulationStatus.NEEDS_REVIEWER_ATTENTION] > 0
    ):
        return ChecklistSectionStatus.YELLOW

    return ChecklistSectionStatus.GREEN


def build_section_summary(
    section_title: str,
    rows: list[PopulatedChecklistRow],
) -> ChecklistSectionSummary:
    """Build one section summary from populated checklist rows."""
    counts = status_counts_for_rows(rows)

    return ChecklistSectionSummary(
        section_title=section_title,
        status=determine_section_status(rows),
        total_rows=len(rows),
        present_rows=counts[ChecklistPopulationStatus.PRESENT],
        missing_rows=counts[ChecklistPopulationStatus.MISSING],
        unclear_rows=counts[ChecklistPopulationStatus.UNCLEAR],
        redacted_rows=counts[ChecklistPopulationStatus.REDACTED],
        needs_reviewer_attention_rows=counts[
            ChecklistPopulationStatus.NEEDS_REVIEWER_ATTENTION
        ],
        optional_not_applicable_rows=counts[
            ChecklistPopulationStatus.NOT_APPLICABLE_OPTIONAL
        ],
    )


def build_section_summaries(
    rows: list[PopulatedChecklistRow],
) -> list[ChecklistSectionSummary]:
    """Build section summaries for all sections represented by rows."""
    section_order: list[str] = []
    rows_by_section: dict[str, list[PopulatedChecklistRow]] = {}

    for row in rows:
        if row.section_title not in rows_by_section:
            section_order.append(row.section_title)
            rows_by_section[row.section_title] = []

        rows_by_section[row.section_title].append(row)

    return [
        build_section_summary(
            section_title=section_title,
            rows=rows_by_section[section_title],
        )
        for section_title in section_order
    ]


def build_populated_checklist(
    *,
    package_name: str,
    rows: list[PopulatedChecklistRow],
) -> PopulatedChecklist:
    """Build a populated checklist with section summaries."""
    return PopulatedChecklist(
        package_name=package_name,
        rows=rows,
        section_summaries=build_section_summaries(rows),
    )

@dataclass
class ChecklistRowRetrievalQuery:
    """Deterministic retrieval query for one checklist row."""

    section_title: str
    checklist_item_id: str
    checklist_item: str
    citation: str = ""
    expected_plan_type: str = ""
    query_text: str = ""
    required_terms: list[str] = field(default_factory=list)
    optional_terms: list[str] = field(default_factory=list)
    reference_queries: list[str] = field(default_factory=list)
    permit_precedent_queries: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Return JSON-serializable query data."""
        return {
            "section_title": self.section_title,
            "checklist_item_id": self.checklist_item_id,
            "checklist_item": self.checklist_item,
            "citation": self.citation,
            "expected_plan_type": self.expected_plan_type,
            "query_text": self.query_text,
            "required_terms": self.required_terms,
            "optional_terms": self.optional_terms,
            "reference_queries": self.reference_queries,
            "permit_precedent_queries": self.permit_precedent_queries,
        }


def normalize_query_part(value: str) -> str:
    """Normalize one query part for deterministic query construction."""
    return " ".join(str(value or "").replace("\n", " ").split())


def unique_nonempty_strings(values: list[str]) -> list[str]:
    """Return unique non-empty strings while preserving order."""
    seen: set[str] = set()
    unique_values: list[str] = []

    for value in values:
        normalized_value = normalize_query_part(value)

        if not normalized_value:
            continue

        dedupe_key = normalized_value.lower()

        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)
        unique_values.append(normalized_value)

    return unique_values


def citation_from_text(value: str) -> str:
    """Extract bracketed CFR citation text from a checklist string, if present."""
    text = str(value or "")
    start = text.find("[")

    if start < 0:
        return ""

    end = text.find("]", start + 1)

    if end < 0:
        return ""

    citation = text[start + 1:end].strip()

    if "CFR" not in citation and "cfr" not in citation:
        return ""

    return citation


def build_checklist_row_query_text(
    *,
    section_title: str,
    item: ReviewChecklistItem,
    citation: str = "",
    expected_plan_type: str = "",
) -> str:
    """Build a deterministic package-retrieval query for one checklist item."""
    parts = [
        section_title,
        item.label,
        item.description,
        citation,
        expected_plan_type.replace("_", " "),
    ]

    parts.extend(item.expected_evidence_terms)

    return " ".join(unique_nonempty_strings(parts))


def build_checklist_row_retrieval_query(
    *,
    checklist: ReviewChecklist,
    item: ReviewChecklistItem,
) -> ChecklistRowRetrievalQuery:
    """Build one retrieval query from a checklist and checklist item."""
    citation = citation_from_text(
        " ".join(
            [
                item.label,
                item.description,
            ]
        )
    )

    required_terms = unique_nonempty_strings(
        [
            item.label,
            item.description,
            citation,
        ]
    )

    optional_terms = unique_nonempty_strings(
        item.expected_evidence_terms
    )

    query_text = build_checklist_row_query_text(
        section_title=checklist.title,
        item=item,
        citation=citation,
        expected_plan_type=checklist.plan_type,
    )

    return ChecklistRowRetrievalQuery(
        section_title=checklist.title,
        checklist_item_id=item.item_id,
        checklist_item=item.label,
        citation=citation,
        expected_plan_type=checklist.plan_type,
        query_text=query_text,
        required_terms=required_terms,
        optional_terms=optional_terms,
        reference_queries=unique_nonempty_strings(item.reference_queries),
        permit_precedent_queries=unique_nonempty_strings(
            item.permit_precedent_queries
        ),
    )


def build_checklist_retrieval_queries(
    checklist: ReviewChecklist,
) -> list[ChecklistRowRetrievalQuery]:
    """Build retrieval queries for every item in a checklist."""
    return [
        build_checklist_row_retrieval_query(
            checklist=checklist,
            item=item,
        )
        for item in checklist.items
    ]