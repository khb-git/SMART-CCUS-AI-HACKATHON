"""
Package-level review model for multi-document Class VI review.

This module does not ingest files. It takes already-temporarily-ingested review
documents, classifies each document, maps them to expected package document
types, and identifies missing or duplicate document types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from review.document_classifier import classify_review_document
from review.package_document_audit import (
    MAIN_DOCUMENT_TYPE_ALIASES,
    audit_package_document_name,
    find_matching_aliases,
)
from review.gap_analysis import GapAnalysisReport, analyze_document_against_checklist
from review.schema import load_default_checklist


REVIEWABLE_INFORMATION_PLAN_TYPES = [
    "project_narrative",
    "site_geologic_characterization",
    "aor_corrective_action",
    "financial_responsibility",
    "well_construction",
    "pre_operational_testing",
    "site_operating",
    "testing_monitoring",
    "injection_well_plugging",
    "pisc_site_closure",
    "emergency_remedial_response",
]


EXPECTED_PACKAGE_PLAN_TYPES = [
    "project_narrative",
    "aor_corrective_action",
    "financial_responsibility",
    "well_construction",
    "pre_operational_testing",
    "testing_monitoring",
    "injection_well_plugging",
    "pisc_site_closure",
    "emergency_remedial_response",
]


REQUIRED_PACKAGE_PLAN_TYPES = [
    "project_narrative",
    "aor_corrective_action",
    "financial_responsibility",
    "well_construction",
    "testing_monitoring",
    "injection_well_plugging",
    "pisc_site_closure",
    "emergency_remedial_response",
]


PACKAGE_COVERAGE_EVIDENCE_TERMS = {
    "financial_responsibility": [
        "financial responsibility",
        "financial assurance",
        "cost estimate",
        "cost estimates",
        "letter of credit",
        "surety bond",
        "trust fund",
        "coverage amount",
        "inflation adjustment",
        "instrument validity",
        "closure cost",
        "plugging cost",
        "corrective action cost",
        "pisc cost",
    ],
    "well_construction": [
        "well construction",
        "well construction plan",
        "well construction details",
        "construction details",
        "casing specifications",
        "preliminary casing specifications",
        "surface casing",
        "long string casing",
        "casing",
        "cement",
        "cementing",
        "tubing",
        "packer",
        "well schematic",
        "injection well construction",
        "cement bond log",
        "cbl",
        "usit",
    ],
    "project_narrative": [
        "project narrative",
        "application narrative",
        "class vi permit application",
        "permit application narrative",
        "project description",
        "facility information",
        "injection project",
        "applicant",
    ],
    "aor_corrective_action": [
        "area of review",
        "corrective action plan",
        "aor and corrective action",
        "aor corrective action",
        "legacy wells",
        "artificial penetrations",
        "computational model",
    ],
}

GENERIC_CROSS_DOCUMENT_TERMS = {
    "monitoring",
    "pressure",
    "temperature",
    "fluid",
    "release",
    "report",
    "records",
    "submitted",
    "documentation",
    "compliance",
    "operator",
    "approval",
    "duration",
    "trigger",
    "threshold",
    "pass",
    "evaluation",
}

CROSS_DOCUMENT_CONTEXT_TERMS = {
    "financial_responsibility": [
        "financial responsibility",
        "financial assurance",
        "cost estimate",
        "cost estimates",
        "coverage amount",
        "letter of credit",
        "surety bond",
        "trust fund",
        "plugging cost",
        "corrective action cost",
        "pisc cost",
        "site closure cost",
        "emergency response cost",
        "inflation adjustment",
        "instrument validity",
    ],
    "injection_well_plugging": [
        "plugging",
        "well plugging",
        "plugging plan",
        "cement plug",
        "plugging materials",
        "post-plugging",
        "site condition",
        "wellhead removal",
        "surface restoration",
        "post-injection site care",
        "site closure",
        "pisc",
    ],
    "pisc_site_closure": [
        "post-injection site care",
        "pisc",
        "site closure",
        "non-endangerment",
        "plume stabilization",
        "pressure front",
        "financial responsibility",
        "financial assurance",
        "cost estimate",
        "coverage amount",
        "closure cost",
    ],
    "well_construction": [
        "well construction",
        "casing",
        "cement",
        "cementing",
        "cement bond log",
        "variable density log",
        "top of cement",
        "acceptance criteria",
        "remedial cementing",
        "mechanical integrity",
    ],
    "aor_corrective_action": [
        "area of review",
        "aor",
        "corrective action",
        "computational model",
        "artificial penetrations",
        "legacy wells",
        "uncertainty",
        "sensitivity",
        "pressure front",
        "plume",
    ],
    "testing_monitoring": [
        "testing and monitoring",
        "monitoring",
        "injection pressure",
        "injection rate",
        "flow rate",
        "groundwater monitoring",
        "plume tracking",
        "pressure-front tracking",
        "surface air",
        "soil gas",
    ],
    "emergency_remedial_response": [
        "emergency",
        "remedial response",
        "trigger",
        "release",
        "excursion",
        "notification",
        "shut-in",
        "restart",
        "resumption",
        "post-event",
        "investigation",
        "monitoring",
    ],
    "project_narrative": [
        "project narrative",
        "class vi permit application",
        "facility information",
        "applicant",
        "indian lands",
        "tribal",
        "project description",
    ],
}

@dataclass
class PackageDocumentReview:
    """Review result for one document inside a package."""

    document_name: str
    document_type: str
    classification_confidence: str
    classification: dict[str, Any]
    covered_plan_types: list[str] = field(default_factory=list)
    coverage_plan_types: list[str] = field(default_factory=list)
    is_combined_document: bool = False
    document_role: str = "main"
    supporting_document_type: str = ""
    report: dict[str, Any] | None = None
    checklist_reports: dict[str, dict[str, Any]] = field(default_factory=dict)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable document review data."""
        return {
            "document_name": self.document_name,
            "document_type": self.document_type,
            "classification_confidence": self.classification_confidence,
            "classification": self.classification,
            "covered_plan_types": self.covered_plan_types,
            "coverage_plan_types": self.coverage_plan_types,
            "is_combined_document": self.is_combined_document,
            "document_role": self.document_role,
            "supporting_document_type": self.supporting_document_type,
            "report": self.report,
            "checklist_reports": self.checklist_reports,
            "error": self.error,
        }

@dataclass
class PackageCoverageEvidence:
    """Evidence explaining why a package plan type was credited."""

    plan_type: str
    document_name: str
    document_type: str
    evidence_source: str
    matched_terms: list[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable package coverage evidence data."""
        return {
            "plan_type": self.plan_type,
            "document_name": self.document_name,
            "document_type": self.document_type,
            "evidence_source": self.evidence_source,
            "matched_terms": self.matched_terms,
            "note": self.note,
        }

@dataclass
class ReviewPackageReport:
    """Package-level review summary for multiple uploaded documents."""

    package_name: str
    overall_status: str
    summary: str
    expected_plan_types: list[str]
    required_plan_types: list[str]
    detected_plan_types: list[str]
    missing_required_plan_types: list[str]
    missing_expected_plan_types: list[str]
    duplicate_plan_types: list[str]
    unknown_documents: list[str]
    supporting_documents: list[str]
    coverage_evidence: list[PackageCoverageEvidence] = field(default_factory=list)
    document_reviews: list[PackageDocumentReview] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable package report data."""
        return {
            "package_name": self.package_name,
            "overall_status": self.overall_status,
            "summary": self.summary,
            "expected_plan_types": self.expected_plan_types,
            "required_plan_types": self.required_plan_types,
            "detected_plan_types": self.detected_plan_types,
            "missing_required_plan_types": self.missing_required_plan_types,
            "missing_expected_plan_types": self.missing_expected_plan_types,
            "duplicate_plan_types": self.duplicate_plan_types,
            "unknown_documents": self.unknown_documents,
            "document_reviews": [
                document_review.to_dict()
                for document_review in self.document_reviews
            ],
            "supporting_documents": self.supporting_documents,
            "coverage_evidence": [
                evidence.to_dict()
                for evidence in self.coverage_evidence
            ],
        }


def document_name(document) -> str:
    """Return the original filename for a temporary review document."""
    return getattr(document, "original_filename", "uploaded_document")

def supporting_document_audit(document) -> tuple[str, str]:
    """Return package document role and supporting type from filename audit."""
    audit_result = audit_package_document_name(document_name(document))

    if audit_result.document_role == "supporting":
        return "supporting", audit_result.document_type

    return "main", ""

def main_document_type_from_filename(document) -> str:
    """Return main document type from filename audit when available."""
    audit_result = audit_package_document_name(document_name(document))

    if audit_result.document_role == "main" and audit_result.document_type != "unknown":
        return audit_result.document_type

    return ""

def filename_has_multiple_main_type_matches(document) -> bool:
    """Return whether the filename clearly mentions multiple main document types."""
    matches = find_matching_aliases(
        document_name(document),
        MAIN_DOCUMENT_TYPE_ALIASES,
    )

    matched_types = {
        document_type
        for document_type, _matched_aliases in matches
        if document_type != "unknown"
    }

    return len(matched_types) > 1

def filename_main_type_matches(document) -> list[str]:
    """Return main document types clearly named in the filename."""
    matches = find_matching_aliases(
        document_name(document),
        MAIN_DOCUMENT_TYPE_ALIASES,
    )

    return sorted(
        {
            document_type
            for document_type, _matched_aliases in matches
            if document_type and document_type != "unknown"
        }
    )


def collect_package_document_text(document, max_chars: int = 100000) -> str:
    """Collect document chunk text for package-level evidence checks."""
    text_parts = [document_name(document)]

    for chunk in getattr(document, "chunks", []) or []:
        text = getattr(chunk, "text", "") or ""

        if text:
            text_parts.append(text)

        if sum(len(part) for part in text_parts) >= max_chars:
            break

    return "\n".join(text_parts)[:max_chars].lower()


def evidence_plan_types_from_text(document) -> list[str]:
    """Return package plan types evidenced somewhere in the document text."""
    text = collect_package_document_text(document)
    evidenced_plan_types = set()

    for plan_type, terms in PACKAGE_COVERAGE_EVIDENCE_TERMS.items():
        matched_terms = [
            term
            for term in terms
            if term.lower() in text
        ]

        # Require at least two weak evidence terms so generic single words like
        # "cement" or "casing" do not over-credit a package topic by themselves.
        if len(matched_terms) >= 2:
            evidenced_plan_types.add(plan_type)

    return sorted(evidenced_plan_types)

def matched_evidence_terms_by_plan_type(document) -> dict[str, list[str]]:
    """Return matched package coverage terms by plan type for one document."""
    text = collect_package_document_text(document)
    matches: dict[str, list[str]] = {}

    for plan_type, terms in PACKAGE_COVERAGE_EVIDENCE_TERMS.items():
        matched_terms = sorted(
            {
                term
                for term in terms
                if term.lower() in text
            }
        )

        if len(matched_terms) >= 2:
            matches[plan_type] = matched_terms

    return matches

def package_coverage_plan_types(
    document,
    document_type: str,
    classification,
    review_plan_types: list[str],
) -> list[str]:
    """Return package completeness topics credited by filename, review, or text evidence."""
    coverage_plan_types = set()

    if document_type and document_type != "unknown":
        coverage_plan_types.add(document_type)

    coverage_plan_types.update(
        plan_type
        for plan_type in review_plan_types
        if plan_type and plan_type != "unknown"
    )

    coverage_plan_types.update(
        plan_type
        for plan_type in getattr(classification, "covered_plan_types", []) or []
        if plan_type and plan_type != "unknown"
    )

    coverage_plan_types.update(filename_main_type_matches(document))
    coverage_plan_types.update(evidence_plan_types_from_text(document))

    return sorted(coverage_plan_types)

def build_document_coverage_evidence(
    document,
    review: PackageDocumentReview,
    classification,
) -> list[PackageCoverageEvidence]:
    """Build coverage evidence rows for one reviewed package document."""
    evidence_rows: list[PackageCoverageEvidence] = []

    filename_matches = set(filename_main_type_matches(document))
    classifier_matches = {
        plan_type
        for plan_type in getattr(classification, "covered_plan_types", []) or []
        if plan_type and plan_type != "unknown"
    }
    text_matches = matched_evidence_terms_by_plan_type(document)

    for plan_type in review.coverage_plan_types:
        if not plan_type or plan_type == "unknown":
            continue

        sources = []

        if plan_type == review.document_type:
            sources.append("primary_document_type")

        if plan_type in review.covered_plan_types:
            sources.append("checklist_review")

        if plan_type in filename_matches:
            sources.append("filename")

        if plan_type in classifier_matches:
            sources.append("classifier")

        if plan_type in text_matches:
            sources.append("text_evidence")

        evidence_source = ", ".join(sources) if sources else "coverage"

        if "text_evidence" in sources:
            note = "Relevant text evidence found; reviewer confirmation recommended."
        elif "filename" in sources:
            note = "Credited from document filename."
        elif "primary_document_type" in sources:
            note = "Credited from the document's primary classification."
        else:
            note = "Credited from package coverage logic."

        evidence_rows.append(
            PackageCoverageEvidence(
                plan_type=plan_type,
                document_name=review.document_name,
                document_type=review.document_type,
                evidence_source=evidence_source,
                matched_terms=text_matches.get(plan_type, []),
                note=note,
            )
        )

    return evidence_rows


def build_package_coverage_evidence(
    documents: list,
    document_reviews: list[PackageDocumentReview],
    classifications: list,
) -> list[PackageCoverageEvidence]:
    """Build package-level coverage evidence rows."""
    evidence_rows: list[PackageCoverageEvidence] = []

    for document, review, classification in zip(
        documents,
        document_reviews,
        classifications,
        strict=False,
    ):
        if review.document_role == "supporting":
            continue

        evidence_rows.extend(
            build_document_coverage_evidence(
                document=document,
                review=review,
                classification=classification,
            )
        )

    return sorted(
        evidence_rows,
        key=lambda row: (row.plan_type, row.document_name, row.evidence_source),
    )

def count_primary_plan_types(
    document_reviews: list[PackageDocumentReview],
) -> dict[str, int]:
    """Count primary known main document types only."""
    counts: dict[str, int] = {}

    for review in document_reviews:
        if review.document_role == "supporting":
            continue

        plan_type = review.document_type

        if not plan_type or plan_type == "unknown":
            continue

        counts[plan_type] = counts.get(plan_type, 0) + 1

    return counts


def count_detected_plan_types(
    document_reviews: list[PackageDocumentReview],
) -> dict[str, int]:
    """Count detected known main document types, including combined coverage."""
    counts: dict[str, int] = {}

    for review in document_reviews:
        if review.document_role == "supporting":
            continue

        coverage_plan_types = (
                review.coverage_plan_types
                or review.covered_plan_types
                or [review.document_type]
        )

        for plan_type in coverage_plan_types:
            if not plan_type or plan_type == "unknown":
                continue

            counts[plan_type] = counts.get(plan_type, 0) + 1

    return counts


def find_duplicate_plan_types(document_reviews: list[PackageDocumentReview]) -> list[str]:
    """Return primary plan types represented by more than one main uploaded document."""
    counts = count_primary_plan_types(document_reviews)

    return sorted(
        plan_type
        for plan_type, count in counts.items()
        if count > 1
    )

def detected_plan_types_from_reviews(
    document_reviews: list[PackageDocumentReview],
) -> list[str]:
    """Return detected main package plan types, including combined-document coverage."""
    detected = set()

    for review in document_reviews:
        if review.document_role == "supporting":
            continue

        coverage_plan_types = (
                review.coverage_plan_types
                or review.covered_plan_types
                or [review.document_type]
        )

        for plan_type in coverage_plan_types:
            if plan_type and plan_type != "unknown":
                detected.add(plan_type)

    return sorted(detected)

def supporting_document_names(
    document_reviews: list[PackageDocumentReview],
) -> list[str]:
    """Return names of documents identified as supporting documents."""
    return sorted(
        review.document_name
        for review in document_reviews
        if review.document_role == "supporting"
    )

def determine_package_status(
    missing_required_plan_types: list[str],
    unknown_documents: list[str],
    document_reviews: list[PackageDocumentReview],
) -> str:
    """Determine package-level readiness status."""
    if missing_required_plan_types:
        return "missing_required_documents"

    if unknown_documents:
        return "needs_review"

    document_statuses = [
        (review.report or {}).get("overall_status", "")
        for review in document_reviews
        if review.report
    ]

    if any(status == "needs_revision" for status in document_statuses):
        return "needs_revision"

    if any(status == "incomplete" for status in document_statuses):
        return "incomplete"

    if any(status == "mostly_complete" for status in document_statuses):
        return "mostly_complete"

    return "package_review_ready"


def build_package_summary(
    detected_plan_types: list[str],
    missing_required_plan_types: list[str],
    missing_expected_plan_types: list[str],
    duplicate_plan_types: list[str],
    unknown_documents: list[str],
    supporting_documents: list[str] | None = None,
) -> str:
    """Build a concise package-level summary."""
    supporting_documents = supporting_documents or []

    return (
        "Package review complete. "
        f"Detected document types: {len(detected_plan_types)}; "
        f"Missing required document types: {len(missing_required_plan_types)}; "
        f"Missing expected document types: {len(missing_expected_plan_types)}; "
        f"Duplicate document types: {len(duplicate_plan_types)}; "
        f"Supporting documents: {len(supporting_documents)}; "
        f"Unknown documents: {len(unknown_documents)}."
    )

def plan_types_to_review(classification) -> list[str]:
    """Return checklist plan types that should be reviewed for one document."""
    covered_plan_types = list(classification.covered_plan_types or [])

    if not covered_plan_types and classification.document_type != "unknown":
        covered_plan_types = [classification.document_type]

    return sorted(
        {
            plan_type
            for plan_type in covered_plan_types
            if plan_type and plan_type != "unknown"
        }
    )


def review_document_against_plan_types(
    document,
    plan_types: list[str],
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Review one document against each requested checklist."""
    checklist_reports: dict[str, dict[str, Any]] = {}
    errors: list[str] = []

    for plan_type in plan_types:
        try:
            checklist = load_default_checklist(plan_type)
            report = analyze_document_against_checklist(document, checklist)
            checklist_reports[plan_type] = report.to_dict()
        except FileNotFoundError as exc:
            errors.append(f"{plan_type}: {exc}")

    return checklist_reports, errors


def primary_report_from_checklist_reports(
    document_type: str,
    checklist_reports: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    """Return the primary report while preserving old single-report compatibility."""
    if document_type in checklist_reports:
        return checklist_reports[document_type]

    if checklist_reports:
        first_plan_type = sorted(checklist_reports)[0]
        return checklist_reports[first_plan_type]

    return None

def review_single_package_document(document) -> PackageDocumentReview:
    """Classify and review one temporarily ingested package document."""
    document_role, supporting_type = supporting_document_audit(document)
    classification = classify_review_document(document)

    document_type = classification.document_type
    classification_dict = classification.to_dict()
    filename_document_type = main_document_type_from_filename(document)

    if filename_document_type and filename_document_type != document_type:
        document_type = filename_document_type
        classification_dict["document_type"] = document_type
        classification_dict["primary_document_type"] = document_type
        classification_dict["reason"] = (
            f"Filename audit identified this document as {document_type}. "
            f"Original classifier reason: {classification.reason}"
        )

    if document_type == "unknown":
        return PackageDocumentReview(
            document_name=document_name(document),
            document_type="unknown",
            classification_confidence=classification.confidence,
            classification=classification_dict,
            covered_plan_types=[],
            coverage_plan_types=[],
            is_combined_document=False,
            document_role=document_role,
            supporting_document_type=supporting_type,
            report=None,
            error="Document type could not be classified.",
        )

    if document_role == "supporting":
        return PackageDocumentReview(
            document_name=document_name(document),
            document_type=document_type,
            classification_confidence=classification.confidence,
            classification=classification_dict,
            covered_plan_types=[],
            coverage_plan_types=[],
            is_combined_document=False,
            document_role=document_role,
            supporting_document_type=supporting_type,
            report=None,
            error="Supporting document detected; no standalone checklist review was run.",
        )

    review_plan_types = plan_types_to_review(classification)
    coverage_plan_types = package_coverage_plan_types(
        document=document,
        document_type=document_type,
        classification=classification,
        review_plan_types=review_plan_types,
    )
    filename_has_multiple_types = filename_has_multiple_main_type_matches(document)

    if filename_document_type and not filename_has_multiple_types:
        review_plan_types = [document_type]
    elif document_type != "unknown" and document_type not in review_plan_types:
        review_plan_types.append(document_type)

    review_plan_types = sorted(set(review_plan_types))
    checklist_reports, errors = review_document_against_plan_types(
        document=document,
        plan_types=review_plan_types,
    )
    primary_report = primary_report_from_checklist_reports(
        document_type=document_type,
        checklist_reports=checklist_reports,
    )

    return PackageDocumentReview(
        document_name=document_name(document),
        document_type=document_type,
        classification_confidence=classification.confidence,
        classification=classification_dict,
        report=primary_report,
        checklist_reports=checklist_reports,
        error="; ".join(errors),
        covered_plan_types=review_plan_types,
        coverage_plan_types=coverage_plan_types,
        is_combined_document=len(review_plan_types) > 1,
        document_role=document_role,
        supporting_document_type=supporting_type,
    )

def finding_context_terms(
    plan_type: str,
    finding: dict[str, Any],
    max_terms: int = 16,
) -> list[str]:
    """Return terms used to search other package documents for related evidence."""
    candidate_terms: list[str] = []

    candidate_terms.extend(CROSS_DOCUMENT_CONTEXT_TERMS.get(plan_type, []))
    candidate_terms.extend(finding.get("matched_terms", []) or [])

    for value in [
        finding.get("label", ""),
        finding.get("item_id", "").replace("_", " "),
    ]:
        value = str(value or "").strip().lower()
        if len(value) >= 5:
            candidate_terms.append(value)

    normalized_terms = []
    seen = set()

    for term in candidate_terms:
        normalized = str(term or "").strip().lower()
        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        normalized_terms.append(normalized)

    return normalized_terms[:max_terms]


def matched_cross_document_terms(
    text: str,
    terms: list[str],
) -> list[str]:
    """Return non-generic terms found in another package document."""
    text = text.lower()

    return sorted(
        {
            term
            for term in terms
            if term
            and term.lower() not in GENERIC_CROSS_DOCUMENT_TERMS
            and term.lower() in text
        }
    )


def build_related_package_evidence_for_finding(
    *,
    source_document_name: str,
    plan_type: str,
    finding: dict[str, Any],
    package_documents: list,
    document_reviews: list[PackageDocumentReview],
    max_documents: int = 3,
    max_terms_per_document: int = 8,
) -> list[dict[str, Any]]:
    """Find related evidence for one finding in other package documents."""
    terms = finding_context_terms(plan_type, finding)

    if not terms:
        return []

    finding_status = finding.get("status", "")

    minimum_matches = 2

    if finding_status == "evidence_found":
        minimum_matches = 3

        has_unconfirmed_groups = bool(
            finding.get("missing_evidence_group_names", [])
            or finding.get("unmatched_evidence_group_names", [])
        )

        is_required_or_critical = (
            finding.get("requirement_level") == "required"
            or finding.get("severity") == "critical"
        )

        if not has_unconfirmed_groups and not is_required_or_critical:
            return []

    related_rows: list[dict[str, Any]] = []

    for document, review in zip(package_documents, document_reviews, strict=False):
        other_document_name = document_name(document)

        if other_document_name == source_document_name:
            continue

        text = collect_package_document_text(document)
        matched_terms = matched_cross_document_terms(text, terms)

        if len(matched_terms) < minimum_matches:
            continue

        related_rows.append(
            {
                "document_name": other_document_name,
                "document_type": review.document_type,
                "evidence_source": "cross_document_text",
                "matched_terms": matched_terms[:max_terms_per_document],
                "note": (
                    "Related package evidence found outside the reviewed document. "
                    "Reviewer should confirm whether this satisfies the checklist item "
                    "or whether an explicit cross-reference is needed."
                ),
            }
        )

        if len(related_rows) >= max_documents:
            break

    return related_rows


def add_cross_document_context_to_findings(
    *,
    package_documents: list,
    document_reviews: list[PackageDocumentReview],
) -> None:
    """Attach related package evidence to missing/evidence_found findings."""
    for review in document_reviews:
        checklist_reports = review.checklist_reports or {}

        for plan_type, checklist_report in checklist_reports.items():
            findings = checklist_report.get("findings", []) or []

            for finding in findings:
                if finding.get("status") != "missing":
                    continue

                related_evidence = build_related_package_evidence_for_finding(
                    source_document_name=review.document_name,
                    plan_type=plan_type,
                    finding=finding,
                    package_documents=package_documents,
                    document_reviews=document_reviews,
                )

                if related_evidence:
                    finding["related_package_evidence"] = related_evidence

def review_document_package(
    documents: list,
    package_name: str = "uploaded_package",
    expected_plan_types: list[str] | None = None,
    required_plan_types: list[str] | None = None,
) -> ReviewPackageReport:
    """Review a package of temporarily ingested documents."""
    if expected_plan_types is None:
        expected_plan_types = EXPECTED_PACKAGE_PLAN_TYPES

    if required_plan_types is None:
        required_plan_types = REQUIRED_PACKAGE_PLAN_TYPES

    classifications = [
        classify_review_document(document)
        for document in documents
    ]

    document_reviews = [
        review_single_package_document(document)
        for document in documents
    ]

    add_cross_document_context_to_findings(
        package_documents=documents,
        document_reviews=document_reviews,
    )

    coverage_evidence = build_package_coverage_evidence(
        documents=documents,
        document_reviews=document_reviews,
        classifications=classifications,
    )

    detected_plan_types = detected_plan_types_from_reviews(document_reviews)

    missing_required_plan_types = sorted(
        plan_type
        for plan_type in required_plan_types
        if plan_type not in detected_plan_types
    )

    missing_expected_plan_types = sorted(
        plan_type
        for plan_type in expected_plan_types
        if plan_type not in detected_plan_types
    )

    duplicate_plan_types = find_duplicate_plan_types(document_reviews)

    unknown_documents = [
        review.document_name
        for review in document_reviews
        if review.document_type == "unknown"
    ]

    supporting_documents = supporting_document_names(document_reviews)

    overall_status = determine_package_status(
        missing_required_plan_types=missing_required_plan_types,
        unknown_documents=unknown_documents,
        document_reviews=document_reviews,
    )

    summary = build_package_summary(
        detected_plan_types=detected_plan_types,
        missing_required_plan_types=missing_required_plan_types,
        missing_expected_plan_types=missing_expected_plan_types,
        duplicate_plan_types=duplicate_plan_types,
        unknown_documents=unknown_documents,
        supporting_documents=supporting_documents,
    )

    return ReviewPackageReport(
        package_name=package_name,
        overall_status=overall_status,
        summary=summary,
        expected_plan_types=expected_plan_types,
        required_plan_types=required_plan_types,
        detected_plan_types=detected_plan_types,
        missing_required_plan_types=missing_required_plan_types,
        missing_expected_plan_types=missing_expected_plan_types,
        duplicate_plan_types=duplicate_plan_types,
        unknown_documents=unknown_documents,
        document_reviews=document_reviews,
        supporting_documents=supporting_documents,
        coverage_evidence=coverage_evidence,
    )