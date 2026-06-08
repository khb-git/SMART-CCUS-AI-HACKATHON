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
from review.package_document_audit import audit_package_document_name
from review.gap_analysis import GapAnalysisReport, analyze_document_against_checklist
from review.schema import load_default_checklist


EXPECTED_PACKAGE_PLAN_TYPES = [
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


REQUIRED_PACKAGE_PLAN_TYPES = [
    "project_narrative",
    "site_geologic_characterization",
    "aor_corrective_action",
    "financial_responsibility",
    "well_construction",
    "site_operating",
    "testing_monitoring",
    "injection_well_plugging",
    "pisc_site_closure",
    "emergency_remedial_response",
]


@dataclass
class PackageDocumentReview:
    """Review result for one document inside a package."""

    document_name: str
    document_type: str
    classification_confidence: str
    classification: dict[str, Any]
    covered_plan_types: list[str] = field(default_factory=list)
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
            "is_combined_document": self.is_combined_document,
            "document_role": self.document_role,
            "supporting_document_type": self.supporting_document_type,
            "report": self.report,
            "checklist_reports": self.checklist_reports,
            "error": self.error,
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

def count_plan_types(document_reviews: list[PackageDocumentReview]) -> dict[str, int]:
    """Count detected known main document types, including combined-document coverage."""
    counts: dict[str, int] = {}

    for review in document_reviews:
        if review.document_role == "supporting":
            continue

        covered_plan_types = review.covered_plan_types or [review.document_type]

        for plan_type in covered_plan_types:
            if not plan_type or plan_type == "unknown":
                continue

            counts[plan_type] = counts.get(plan_type, 0) + 1

    return counts


def find_duplicate_plan_types(document_reviews: list[PackageDocumentReview]) -> list[str]:
    """Return plan types represented by more than one uploaded document."""
    counts = count_plan_types(document_reviews)

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

        covered_plan_types = review.covered_plan_types or [review.document_type]

        for plan_type in covered_plan_types:
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

    if document_type == "unknown":
        return PackageDocumentReview(
            document_name=document_name(document),
            document_type="unknown",
            classification_confidence=classification.confidence,
            classification=classification_dict,
            covered_plan_types=[],
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
            is_combined_document=False,
            document_role=document_role,
            supporting_document_type=supporting_type,
            report=None,
            error="Supporting document detected; no standalone checklist review was run.",
        )

    review_plan_types = plan_types_to_review(classification)
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
        covered_plan_types=classification.covered_plan_types,
        is_combined_document=classification.is_combined_document,
        document_role=document_role,
        supporting_document_type=supporting_type,
    )


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

    document_reviews = [
        review_single_package_document(document)
        for document in documents
    ]

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
    )