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

REDACTED_TEXT_MARKERS = [
    "redacted",
    "redaction",
    "withheld",
    "confidential",
    "confidential business information",
    "cbi",
    "[redacted]",
    "(redacted)",
]


def package_finding_candidate_text(finding: dict) -> str:
    """Collect searchable text from one package review finding."""
    parts = [
        finding.get("item_id", ""),
        finding.get("label", ""),
        finding.get("finding", ""),
        finding.get("recommended_fix", ""),
        finding.get("status", ""),
        finding.get("confidence", ""),
        finding.get("document_name", ""),
    ]

    parts.extend(finding.get("matched_terms", []) or [])
    parts.extend(finding.get("supporting_excerpts", []) or [])

    for location in finding.get("evidence_locations", []) or []:
        parts.append(location.get("file_name", ""))
        parts.append(str(location.get("page_number", "") or ""))
        parts.append(location.get("excerpt", ""))

    return "\n".join(str(part or "") for part in parts)


def normalized_contains(text: str, term: str) -> bool:
    """Return whether normalized text contains a normalized term."""
    normalized_text = normalize_query_part(text).lower()
    normalized_term = normalize_query_part(term).lower()

    return bool(normalized_term) and normalized_term in normalized_text


def text_has_redaction_marker(text: str) -> bool:
    """Return whether text includes a redaction or confidentiality marker."""
    return any(
        normalized_contains(text, marker)
        for marker in REDACTED_TEXT_MARKERS
    )


def score_query_against_package_finding(
    query: ChecklistRowRetrievalQuery,
    finding: dict,
) -> int:
    """Score how well one package finding matches a checklist row query."""
    text = package_finding_candidate_text(finding)
    score = 0

    if normalized_contains(text, query.checklist_item_id):
        score += 5

    if query.citation and normalized_contains(text, query.citation):
        score += 4

    for term in query.optional_terms:
        if normalized_contains(text, term):
            score += 2

    for term in query.required_terms:
        if normalized_contains(text, term):
            score += 1

    if query.expected_plan_type and normalized_contains(
        text,
        query.expected_plan_type.replace("_", " "),
    ):
        score += 1

    return score


def choose_best_package_finding(
    query: ChecklistRowRetrievalQuery,
    package_findings: list[dict],
    minimum_score: int = 2,
) -> dict | None:
    """Choose the best package finding for a checklist row query."""
    best_finding: dict | None = None
    best_score = 0

    for finding in package_findings:
        score = score_query_against_package_finding(
            query=query,
            finding=finding,
        )

        if score > best_score:
            best_score = score
            best_finding = finding

    if best_score < minimum_score:
        return None

    return best_finding


def first_package_evidence_location(finding: dict) -> dict:
    """Return the first evidence location for a package finding."""
    locations = finding.get("evidence_locations", []) or []

    if not locations:
        return {}

    return locations[0] or {}


def populated_evidence_from_package_finding(
    finding: dict,
) -> list[PopulatedChecklistEvidence]:
    """Convert package finding evidence locations to populated checklist evidence."""
    evidence_items: list[PopulatedChecklistEvidence] = []
    locations = finding.get("evidence_locations", []) or []

    if locations:
        for location in locations:
            evidence_items.append(
                PopulatedChecklistEvidence(
                    file_name=(
                        location.get("file_name")
                        or finding.get("document_name", "")
                    ),
                    page_number=location.get("page_number"),
                    excerpt=location.get("excerpt", ""),
                    source_label=finding.get("label", ""),
                    confidence=finding.get("confidence", "Low"),
                )
            )

        return evidence_items

    excerpts = finding.get("supporting_excerpts", []) or []

    for excerpt in excerpts:
        evidence_items.append(
            PopulatedChecklistEvidence(
                file_name=finding.get("document_name", ""),
                page_number=None,
                excerpt=excerpt,
                source_label=finding.get("label", ""),
                confidence=finding.get("confidence", "Low"),
            )
        )

    return evidence_items


def infer_checklist_population_status_from_finding(
    finding: dict,
) -> ChecklistPopulationStatus:
    """Infer populated checklist row status from an existing package finding."""
    text = package_finding_candidate_text(finding)
    raw_status = normalize_query_part(str(finding.get("status", ""))).lower()
    raw_finding = normalize_query_part(str(finding.get("finding", ""))).lower()

    if text_has_redaction_marker(text):
        return ChecklistPopulationStatus.REDACTED

    if raw_status in {"missing", "missing_evidence", "not_found"}:
        return ChecklistPopulationStatus.MISSING

    if raw_status in {"unclear", "needs_review", "needs_reviewer_attention"}:
        return ChecklistPopulationStatus.NEEDS_REVIEWER_ATTENTION

    missing_phrases = [
        "does not provide",
        "does not identify",
        "does not document",
        "not provided",
        "not identified",
        "missing",
        "no clear",
    ]

    if any(phrase in raw_finding for phrase in missing_phrases):
        return ChecklistPopulationStatus.MISSING

    evidence_locations = finding.get("evidence_locations", []) or []
    supporting_excerpts = finding.get("supporting_excerpts", []) or []

    if evidence_locations or supporting_excerpts:
        return ChecklistPopulationStatus.PRESENT

    return ChecklistPopulationStatus.UNCLEAR


def populate_checklist_row_from_query(
    *,
    query: ChecklistRowRetrievalQuery,
    package_findings: list[dict],
) -> PopulatedChecklistRow:
    """Populate one checklist row from existing package review findings."""
    finding = choose_best_package_finding(
        query=query,
        package_findings=package_findings,
    )

    if finding is None:
        return PopulatedChecklistRow(
            section_title=query.section_title,
            checklist_item=query.checklist_item,
            citation=query.citation,
            status=ChecklistPopulationStatus.MISSING,
            system_notes=(
                "No matching package review evidence was found for this checklist row."
            ),
        )

    evidence_items = populated_evidence_from_package_finding(finding)
    first_location = first_package_evidence_location(finding)
    first_evidence = evidence_items[0] if evidence_items else None

    file_name = ""
    page_number = None
    evidence_excerpt = ""

    if first_evidence is not None:
        file_name = first_evidence.file_name
        page_number = first_evidence.page_number
        evidence_excerpt = first_evidence.excerpt
    elif first_location:
        file_name = first_location.get("file_name", "")
        page_number = first_location.get("page_number")
        evidence_excerpt = first_location.get("excerpt", "")

    return PopulatedChecklistRow(
        section_title=query.section_title,
        checklist_item=query.checklist_item,
        citation=query.citation,
        status=infer_checklist_population_status_from_finding(finding),
        gsdt_module_folder=query.expected_plan_type.replace("_", " "),
        file_name=file_name,
        page_number=page_number,
        evidence_excerpt=evidence_excerpt,
        system_notes=(
            "Populated from existing package review evidence."
        ),
        reviewer_notes="",
        reviewer_confirmation=ReviewerConfirmationStatus.PENDING_REVIEW,
        confidence=finding.get("confidence", "Low"),
        evidence=evidence_items,
    )


def collect_package_review_findings_for_population(
    package_report: dict,
) -> list[dict]:
    """Collect package review findings from a package report dictionary."""
    collected: list[dict] = []

    for finding in package_report.get("findings", []) or []:
        collected.append(dict(finding))

    for document_review in package_report.get("document_reviews", []) or []:
        document_name = document_review.get("document_name", "")
        checklist_reports = document_review.get("checklist_reports", {}) or {}

        if not checklist_reports and document_review.get("report"):
            report = document_review.get("report") or {}
            plan_type = report.get(
                "plan_type",
                document_review.get("document_type", "unknown"),
            )
            checklist_reports = {plan_type: report}

        for checklist_report in checklist_reports.values():
            for finding in checklist_report.get("findings", []) or []:
                finding_copy = dict(finding)
                finding_copy.setdefault("document_name", document_name)
                collected.append(finding_copy)

    return collected


def build_populated_checklist_from_package_report(
    *,
    package_name: str,
    checklists: list[ReviewChecklist],
    package_report: dict,
) -> PopulatedChecklist:
    """Build a populated checklist from existing package review findings."""
    package_findings = collect_package_review_findings_for_population(
        package_report
    )

    rows: list[PopulatedChecklistRow] = []

    for checklist in checklists:
        for query in build_checklist_retrieval_queries(checklist):
            rows.append(
                populate_checklist_row_from_query(
                    query=query,
                    package_findings=package_findings,
                )
            )

    return build_populated_checklist(
        package_name=package_name,
        rows=rows,
    )

CHECKLIST_STATUS_LABELS = {
    ChecklistPopulationStatus.PRESENT: "Present",
    ChecklistPopulationStatus.MISSING: "Missing",
    ChecklistPopulationStatus.UNCLEAR: "Unclear",
    ChecklistPopulationStatus.REDACTED: "Redacted",
    ChecklistPopulationStatus.NEEDS_REVIEWER_ATTENTION: (
        "Needs reviewer attention"
    ),
    ChecklistPopulationStatus.NOT_APPLICABLE_OPTIONAL: (
        "Not applicable / optional"
    ),
}


CHECKLIST_SECTION_STATUS_LABELS = {
    ChecklistSectionStatus.GREEN: "Green",
    ChecklistSectionStatus.YELLOW: "Yellow",
    ChecklistSectionStatus.RED: "Red",
    ChecklistSectionStatus.GRAY: "Gray",
}


def checklist_status_label(status: ChecklistPopulationStatus) -> str:
    """Return reviewer-facing label for a populated checklist row status."""
    return CHECKLIST_STATUS_LABELS.get(status, status.value)


def checklist_section_status_label(status: ChecklistSectionStatus) -> str:
    """Return reviewer-facing label for a checklist section status."""
    return CHECKLIST_SECTION_STATUS_LABELS.get(status, status.value)


def markdown_escape_cell(value: object) -> str:
    """Escape simple Markdown table cell content."""
    text = str(value if value is not None else "")
    text = text.replace("\n", " ")
    text = text.replace("|", "\\|")
    return " ".join(text.split())


def format_page_number(page_number: int | None) -> str:
    """Format optional page number for reviewer-facing output."""
    if page_number is None:
        return ""

    return str(page_number)


def format_checklist_row_heading(row: PopulatedChecklistRow, index: int) -> str:
    """Format one checklist row heading."""
    return f"### {index}. {row.checklist_item}"


def build_markdown_populated_checklist_summary(
    checklist: PopulatedChecklist,
) -> str:
    """Build Markdown summary block for a populated checklist."""
    total_rows = len(checklist.rows)
    total_sections = len(checklist.section_summaries)

    status_counts = status_counts_for_rows(checklist.rows)

    return "\n".join(
        [
            f"# Populated Class VI Completeness Checklist: {checklist.package_name}",
            "",
            "## Package Summary",
            "",
            f"- Package name: `{checklist.package_name}`",
            f"- Checklist sections: {total_sections}",
            f"- Checklist rows: {total_rows}",
            f"- Present rows: {status_counts[ChecklistPopulationStatus.PRESENT]}",
            f"- Missing rows: {status_counts[ChecklistPopulationStatus.MISSING]}",
            f"- Unclear rows: {status_counts[ChecklistPopulationStatus.UNCLEAR]}",
            f"- Redacted rows: {status_counts[ChecklistPopulationStatus.REDACTED]}",
            (
                "- Needs reviewer attention rows: "
                f"{status_counts[ChecklistPopulationStatus.NEEDS_REVIEWER_ATTENTION]}"
            ),
            (
                "- Optional / not applicable rows: "
                f"{status_counts[ChecklistPopulationStatus.NOT_APPLICABLE_OPTIONAL]}"
            ),
            "",
        ]
    )


def build_markdown_section_summary_table(
    checklist: PopulatedChecklist,
) -> str:
    """Build Markdown table of section summaries."""
    lines = [
        "## Section Summary",
        "",
        "| Section | Status | Total | Present | Missing | Unclear | Redacted | Reviewer Attention | Optional / N/A |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for summary in checklist.section_summaries:
        lines.append(
            "| "
            f"{markdown_escape_cell(summary.section_title)} | "
            f"{checklist_section_status_label(summary.status)} | "
            f"{summary.total_rows} | "
            f"{summary.present_rows} | "
            f"{summary.missing_rows} | "
            f"{summary.unclear_rows} | "
            f"{summary.redacted_rows} | "
            f"{summary.needs_reviewer_attention_rows} | "
            f"{summary.optional_not_applicable_rows} |"
        )

    lines.append("")

    return "\n".join(lines)


def build_markdown_checklist_row(row: PopulatedChecklistRow, index: int) -> str:
    """Build Markdown for one populated checklist row."""
    lines = [
        format_checklist_row_heading(row, index),
        "",
        f"- Status: **{checklist_status_label(row.status)}**",
        f"- Citation: {row.citation or 'Not specified'}",
        f"- GSDT Module/Folder: {row.gsdt_module_folder or ''}",
        f"- File Name: {row.file_name or ''}",
        f"- Page Number: {format_page_number(row.page_number)}",
        f"- Confidence: {row.confidence}",
        f"- Reviewer confirmation: {row.reviewer_confirmation.value}",
        "",
        "**Evidence excerpt**",
        "",
        row.evidence_excerpt or "_No evidence excerpt populated._",
        "",
        "**System notes**",
        "",
        row.system_notes or "_No system notes._",
        "",
        "**Reviewer notes**",
        "",
        row.reviewer_notes or "_No reviewer notes._",
        "",
    ]

    if row.evidence:
        lines.extend(
            [
                "**Evidence locations**",
                "",
                "| File | Page | Confidence | Excerpt |",
                "|---|---:|---|---|",
            ]
        )

        for evidence in row.evidence:
            lines.append(
                "| "
                f"{markdown_escape_cell(evidence.file_name)} | "
                f"{markdown_escape_cell(format_page_number(evidence.page_number))} | "
                f"{markdown_escape_cell(evidence.confidence)} | "
                f"{markdown_escape_cell(evidence.excerpt)} |"
            )

        lines.append("")

    return "\n".join(lines)


def build_markdown_populated_checklist_rows(
    checklist: PopulatedChecklist,
) -> str:
    """Build Markdown grouped checklist rows by section."""
    lines: list[str] = [
        "## Populated Checklist Rows",
        "",
    ]

    current_section = ""

    for index, row in enumerate(checklist.rows, start=1):
        if row.section_title != current_section:
            current_section = row.section_title
            lines.extend(
                [
                    f"## {current_section}",
                    "",
                ]
            )

        lines.append(
            build_markdown_checklist_row(
                row=row,
                index=index,
            )
        )

    return "\n".join(lines)


def build_markdown_populated_checklist(
    checklist: PopulatedChecklist,
) -> str:
    """Build a reviewer-facing Markdown populated checklist export."""
    sections = [
        build_markdown_populated_checklist_summary(checklist),
        build_markdown_section_summary_table(checklist),
        build_markdown_populated_checklist_rows(checklist),
    ]

    return "\n".join(section.rstrip() for section in sections).strip() + "\n"