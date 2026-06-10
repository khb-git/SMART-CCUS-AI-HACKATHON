"""
Package document type audit helpers.

This module maps scraped permit-package filenames to supported review
document/checklist types. It is intentionally filename-based so we can audit
real scraped packages before changing checklist logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


MAIN_DOCUMENT_TYPE_ALIASES = {
    "project_narrative": [
        "narrative",
        "project narrative",
        "application narrative",
    ],
    "aor_corrective_action": [
        "aor and corrective action",
        "area of review and corrective action",
        "corrective action plan",
    ],
    "financial_responsibility": [
        "cost estimates",
        "cost estimate",
        "financial responsibility",
        "financial assurance",
    ],
    "emergency_remedial_response": [
        "errp",
        "emergency and remedial response",
        "emergency remedial response",
        "emergency response plan",
    ],
    "injection_well_plugging": [
        "injection well plugging plan",
        "well plugging plan",
        "plugging plan",
    ],
        "pisc_site_closure": [
        "pisc",
        "pisc and site closure plan",
        "post injection site care",
        "post-injection site care",
        "post injection site care and site closure",
        "post-injection site care and site closure",
        "site closure plan",
    ],
    "pre_operational_testing": [
        "pre operational testing",
        "pre-operational testing",
        "pre operational testing plan",
        "pre-operational testing plan",
    ],
    "site_operating": [
        "site operating plan",
        "operating plan",
        "site operations plan",
    ],
    "site_geologic_characterization": [
        "site geologic characterization",
        "geologic characterization",
        "site characterization",
    ],
    "testing_monitoring": [
        "testing and monitoring plan",
        "testing monitoring plan",
        "testing and monitoring",
    ],
    "well_construction": [
        "well construction plan",
        "well construction",
    ],
}


SUPPORTING_DOCUMENT_TYPE_ALIASES = {
    "supporting_pisc_alternative_timeframe": [
        "alternative pisc timeframe",
        "alternative post injection site care timeframe",
        "alternative post-injection site care timeframe",
        "alternative pisc timeline",
    ],
}


@dataclass
class PackageDocumentAuditResult:
    """Filename audit result for one package document."""

    document_name: str
    path: str
    document_type: str
    document_role: str
    matched_aliases: list[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable audit result data."""
        return {
            "document_name": self.document_name,
            "path": self.path,
            "document_type": self.document_type,
            "document_role": self.document_role,
            "matched_aliases": self.matched_aliases,
            "reason": self.reason,
        }


@dataclass
class PackageDocumentAuditReport:
    """Audit report for a set of scraped package documents."""

    package_name: str
    audited_documents: list[PackageDocumentAuditResult]
    detected_main_document_types: list[str]
    detected_supporting_document_types: list[str]
    unknown_documents: list[str]
    missing_expected_main_document_types: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable package audit report data."""
        return {
            "package_name": self.package_name,
            "audited_documents": [
                result.to_dict()
                for result in self.audited_documents
            ],
            "detected_main_document_types": self.detected_main_document_types,
            "detected_supporting_document_types": self.detected_supporting_document_types,
            "unknown_documents": self.unknown_documents,
            "missing_expected_main_document_types": self.missing_expected_main_document_types,
        }


def normalize_filename(value: str) -> str:
    """Normalize filename text for alias matching."""
    path = Path(str(value or ""))
    stem = path.stem

    # Scraped files often end with __hash. Remove that suffix for cleaner matching.
    if "__" in stem:
        stem = stem.split("__", 1)[0]

    return " ".join(
        stem.lower()
        .replace("-", " ")
        .replace("_", " ")
        .replace("/", " ")
        .replace("\\", " ")
        .split()
    )


def find_matching_aliases(
    filename: str,
    aliases_by_type: dict[str, list[str]],
) -> list[tuple[str, list[str]]]:
    """Return document types whose aliases match a filename."""
    normalized = normalize_filename(filename)
    matches = []

    for document_type, aliases in aliases_by_type.items():
        matched_aliases = [
            alias
            for alias in aliases
            if normalize_filename(alias) in normalized
        ]

        if matched_aliases:
            matches.append((document_type, matched_aliases))

    return matches


def choose_best_match(
    matches: list[tuple[str, list[str]]],
) -> tuple[str, list[str]]:
    """Choose the strongest filename match from candidate aliases."""
    if not matches:
        return "unknown", []

    return sorted(
        matches,
        key=lambda item: max(len(normalize_filename(alias)) for alias in item[1]),
        reverse=True,
    )[0]


def audit_package_document_name(path: str | Path) -> PackageDocumentAuditResult:
    """Audit one document filename into main, supporting, or unknown role."""
    path = Path(path)
    document_name = path.name

    supporting_matches = find_matching_aliases(
        document_name,
        SUPPORTING_DOCUMENT_TYPE_ALIASES,
    )

    if supporting_matches:
        document_type, matched_aliases = choose_best_match(supporting_matches)

        return PackageDocumentAuditResult(
            document_name=document_name,
            path=str(path),
            document_type=document_type,
            document_role="supporting",
            matched_aliases=matched_aliases,
            reason="Matched filename to a supporting package document type.",
        )

    main_matches = find_matching_aliases(
        document_name,
        MAIN_DOCUMENT_TYPE_ALIASES,
    )

    if main_matches:
        document_type, matched_aliases = choose_best_match(main_matches)

        return PackageDocumentAuditResult(
            document_name=document_name,
            path=str(path),
            document_type=document_type,
            document_role="main",
            matched_aliases=matched_aliases,
            reason="Matched filename to a main checklist document type.",
        )

    return PackageDocumentAuditResult(
        document_name=document_name,
        path=str(path),
        document_type="unknown",
        document_role="unknown",
        matched_aliases=[],
        reason="No filename alias matched a supported package document type.",
    )


def audit_package_documents(
    paths: list[str | Path],
    package_name: str = "scraped_package",
    expected_main_document_types: list[str] | None = None,
) -> PackageDocumentAuditReport:
    """Audit a package document list against supported checklist document types."""
    if expected_main_document_types is None:
        expected_main_document_types = sorted(MAIN_DOCUMENT_TYPE_ALIASES)

    audited_documents = [
        audit_package_document_name(path)
        for path in paths
    ]

    detected_main_document_types = sorted(
        {
            result.document_type
            for result in audited_documents
            if result.document_role == "main"
        }
    )

    detected_supporting_document_types = sorted(
        {
            result.document_type
            for result in audited_documents
            if result.document_role == "supporting"
        }
    )

    unknown_documents = sorted(
        result.document_name
        for result in audited_documents
        if result.document_role == "unknown"
    )

    missing_expected_main_document_types = sorted(
        document_type
        for document_type in expected_main_document_types
        if document_type not in detected_main_document_types
    )

    return PackageDocumentAuditReport(
        package_name=package_name,
        audited_documents=audited_documents,
        detected_main_document_types=detected_main_document_types,
        detected_supporting_document_types=detected_supporting_document_types,
        unknown_documents=unknown_documents,
        missing_expected_main_document_types=missing_expected_main_document_types,
    )


def find_package_files(
    root: str | Path,
    package_terms: list[str],
    suffixes: set[str] | None = None,
) -> list[Path]:
    """Find package files below a root using package name terms."""
    root = Path(root)

    if suffixes is None:
        suffixes = {".pdf", ".docx", ".xlsx"}

    if not root.exists():
        return []

    normalized_terms = [
        normalize_filename(term)
        for term in package_terms
    ]

    matches = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in suffixes:
            continue

        normalized_name = normalize_filename(path.name)

        if any(term in normalized_name for term in normalized_terms):
            matches.append(path)

    return sorted(matches)