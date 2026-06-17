"""Deterministic MAIP cross-reference validation.

This module validates Maximum Allowable Injection Pressure evidence from
structured inputs. It does not use an LLM, RAG, or broad numeric extraction.

Architecture:
    Backend decides.
    Reviewer confirms.
    LLM explains.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

class MaipValidationStatus(str, Enum):
    """Status for one deterministic MAIP validation finding."""

    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"
    MISSING_EVIDENCE = "missing_evidence"


class MaipValidationSeverity(str, Enum):
    """Reviewer-facing severity for MAIP validation findings."""

    INFO = "info"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MaipEvidenceValue:
    """One structured value used by the MAIP validator."""

    concept: str
    value: float | None = None
    unit: str = "psi"
    source_file: str = ""
    page_number: int | None = None
    excerpt: str = ""
    confidence: str = "Low"
    source_finding_id: str = ""
    source_label: str = ""
    matched_term: str = ""
    extraction_method: str = "manual_structured_input"
    extraction_notes: str = ""

    def to_dict(self) -> dict:
        """Return JSON-serializable evidence value data."""
        return {
            "concept": self.concept,
            "value": self.value,
            "unit": self.unit,
            "source_file": self.source_file,
            "page_number": self.page_number,
            "excerpt": self.excerpt,
            "confidence": self.confidence,
            "source_finding_id": self.source_finding_id,
            "source_label": self.source_label,
            "matched_term": self.matched_term,
            "extraction_method": self.extraction_method,
            "extraction_notes": self.extraction_notes,
        }


@dataclass
class MaipValidationInput:
    """Structured input for deterministic MAIP validation."""

    proposed_maip: MaipEvidenceValue | None = None
    fracture_pressure: MaipEvidenceValue | None = None
    fracture_gradient: MaipEvidenceValue | None = None
    aor_model_max_pressure: MaipEvidenceValue | None = None
    casing_pressure_rating: MaipEvidenceValue | None = None
    annulus_pressure_limit: MaipEvidenceValue | None = None
    operating_pressure_limit: MaipEvidenceValue | None = None
    annulus_management_evidence: MaipEvidenceValue | None = None
    operating_margin_evidence: MaipEvidenceValue | None = None


@dataclass
class MaipValidationFinding:
    """One deterministic MAIP validation finding."""

    finding_id: str
    status: MaipValidationStatus
    severity: MaipValidationSeverity
    message: str
    recommended_action: str
    supporting_values: list[MaipEvidenceValue] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Return JSON-serializable finding data."""
        return {
            "finding_id": self.finding_id,
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "recommended_action": self.recommended_action,
            "supporting_values": [
                value.to_dict()
                for value in self.supporting_values
            ],
        }


@dataclass
class MaipValidationReport:
    """Complete deterministic MAIP validation report."""

    overall_status: MaipValidationStatus
    summary: str
    findings: list[MaipValidationFinding]

    def to_dict(self) -> dict:
        """Return JSON-serializable report data."""
        return {
            "overall_status": self.overall_status.value,
            "summary": self.summary,
            "findings": [
                finding.to_dict()
                for finding in self.findings
            ],
        }


def has_numeric_value(value: MaipEvidenceValue | None) -> bool:
    """Return whether an evidence value contains a usable numeric value."""
    return value is not None and value.value is not None


def available_values(*values: MaipEvidenceValue | None) -> list[MaipEvidenceValue]:
    """Return non-empty values for supporting evidence display."""
    return [value for value in values if value is not None]


def validate_maip_evidence_present(
    validation_input: MaipValidationInput,
) -> MaipValidationFinding:
    """Validate that proposed MAIP evidence is present."""
    if not has_numeric_value(validation_input.proposed_maip):
        return MaipValidationFinding(
            finding_id="maip_evidence_present",
            status=MaipValidationStatus.MISSING_EVIDENCE,
            severity=MaipValidationSeverity.HIGH,
            message=(
                "The package does not provide a clear proposed Maximum "
                "Allowable Injection Pressure."
            ),
            recommended_action=(
                "Reviewer should request or locate the proposed MAIP value "
                "before accepting the operating pressure basis."
            ),
            supporting_values=available_values(validation_input.proposed_maip),
        )

    return MaipValidationFinding(
        finding_id="maip_evidence_present",
        status=MaipValidationStatus.PASS,
        severity=MaipValidationSeverity.INFO,
        message="Proposed MAIP evidence is present.",
        recommended_action=(
            "Reviewer should confirm the cited MAIP value and source location."
        ),
        supporting_values=available_values(validation_input.proposed_maip),
    )


def validate_fracture_pressure_evidence_present(
    validation_input: MaipValidationInput,
) -> MaipValidationFinding:
    """Validate that fracture-pressure basis evidence is present."""
    if (
        not has_numeric_value(validation_input.fracture_pressure)
        and not has_numeric_value(validation_input.fracture_gradient)
    ):
        return MaipValidationFinding(
            finding_id="fracture_pressure_evidence_present",
            status=MaipValidationStatus.MISSING_EVIDENCE,
            severity=MaipValidationSeverity.HIGH,
            message=(
                "The package does not provide clear fracture pressure or "
                "fracture gradient evidence needed to verify the proposed MAIP."
            ),
            recommended_action=(
                "Reviewer should request fracture pressure, fracture gradient, "
                "or equivalent limiting-pressure evidence."
            ),
            supporting_values=available_values(
                validation_input.fracture_pressure,
                validation_input.fracture_gradient,
            ),
        )

    return MaipValidationFinding(
        finding_id="fracture_pressure_evidence_present",
        status=MaipValidationStatus.PASS,
        severity=MaipValidationSeverity.INFO,
        message="Fracture pressure or fracture gradient evidence is present.",
        recommended_action=(
            "Reviewer should confirm the fracture-pressure basis and units."
        ),
        supporting_values=available_values(
            validation_input.fracture_pressure,
            validation_input.fracture_gradient,
        ),
    )


def validate_maip_below_fracture_pressure_limit(
    validation_input: MaipValidationInput,
) -> MaipValidationFinding:
    """Validate proposed MAIP against 90 percent of fracture pressure."""
    proposed_maip = validation_input.proposed_maip
    fracture_pressure = validation_input.fracture_pressure

    if not has_numeric_value(proposed_maip) or not has_numeric_value(fracture_pressure):
        return MaipValidationFinding(
            finding_id="maip_below_90_percent_fracture_pressure",
            status=MaipValidationStatus.MISSING_EVIDENCE,
            severity=MaipValidationSeverity.HIGH,
            message=(
                "The package does not provide enough numeric evidence to compare "
                "proposed MAIP against 90% of fracture pressure."
            ),
            recommended_action=(
                "Reviewer should confirm both proposed MAIP and fracture pressure."
            ),
            supporting_values=available_values(proposed_maip, fracture_pressure),
        )

    threshold = 0.90 * float(fracture_pressure.value)

    if float(proposed_maip.value) > threshold:
        return MaipValidationFinding(
            finding_id="maip_below_90_percent_fracture_pressure",
            status=MaipValidationStatus.FAIL,
            severity=MaipValidationSeverity.CRITICAL,
            message=(
                "The proposed MAIP exceeds 90% of the cited fracture pressure."
            ),
            recommended_action=(
                "Reviewer should require a revised MAIP or supporting technical "
                "basis before accepting the operating pressure limit."
            ),
            supporting_values=available_values(proposed_maip, fracture_pressure),
        )

    narrow_margin_threshold = 0.85 * float(fracture_pressure.value)

    if float(proposed_maip.value) > narrow_margin_threshold:
        return MaipValidationFinding(
            finding_id="maip_below_90_percent_fracture_pressure",
            status=MaipValidationStatus.WARNING,
            severity=MaipValidationSeverity.MODERATE,
            message=(
                "The proposed MAIP is below the 90% fracture-pressure limit but "
                "has a narrow operating margin."
            ),
            recommended_action=(
                "Reviewer should confirm the margin is acceptable and supported "
                "by the operating and monitoring plan."
            ),
            supporting_values=available_values(proposed_maip, fracture_pressure),
        )

    return MaipValidationFinding(
        finding_id="maip_below_90_percent_fracture_pressure",
        status=MaipValidationStatus.PASS,
        severity=MaipValidationSeverity.INFO,
        message="The proposed MAIP is below 90% of the cited fracture pressure.",
        recommended_action=(
            "Reviewer should confirm the cited values, units, and source evidence."
        ),
        supporting_values=available_values(proposed_maip, fracture_pressure),
    )


def validate_maip_within_aor_model_pressure(
    validation_input: MaipValidationInput,
) -> MaipValidationFinding:
    """Validate proposed MAIP against AoR model pressure assumptions."""
    proposed_maip = validation_input.proposed_maip
    aor_pressure = validation_input.aor_model_max_pressure

    if not has_numeric_value(proposed_maip) or not has_numeric_value(aor_pressure):
        return MaipValidationFinding(
            finding_id="maip_within_aor_model_pressure",
            status=MaipValidationStatus.MISSING_EVIDENCE,
            severity=MaipValidationSeverity.HIGH,
            message=(
                "The package does not provide enough numeric evidence to compare "
                "proposed MAIP against the AoR model pressure assumption."
            ),
            recommended_action=(
                "Reviewer should confirm the proposed MAIP and the maximum "
                "pressure represented in the AoR model."
            ),
            supporting_values=available_values(proposed_maip, aor_pressure),
        )

    if float(proposed_maip.value) > float(aor_pressure.value):
        return MaipValidationFinding(
            finding_id="maip_within_aor_model_pressure",
            status=MaipValidationStatus.FAIL,
            severity=MaipValidationSeverity.HIGH,
            message=(
                "The proposed MAIP exceeds the pressure constraint represented "
                "in the AoR model evidence."
            ),
            recommended_action=(
                "Reviewer should request reconciliation between the operating "
                "pressure limit and AoR model assumptions."
            ),
            supporting_values=available_values(proposed_maip, aor_pressure),
        )

    return MaipValidationFinding(
        finding_id="maip_within_aor_model_pressure",
        status=MaipValidationStatus.PASS,
        severity=MaipValidationSeverity.INFO,
        message="The proposed MAIP is within the cited AoR model pressure assumption.",
        recommended_action=(
            "Reviewer should confirm the AoR model pressure basis and source evidence."
        ),
        supporting_values=available_values(proposed_maip, aor_pressure),
    )


def validate_maip_below_casing_rating(
    validation_input: MaipValidationInput,
) -> MaipValidationFinding:
    """Validate proposed MAIP against casing pressure rating."""
    proposed_maip = validation_input.proposed_maip
    casing_rating = validation_input.casing_pressure_rating

    if not has_numeric_value(proposed_maip) or not has_numeric_value(casing_rating):
        return MaipValidationFinding(
            finding_id="maip_below_casing_pressure_rating",
            status=MaipValidationStatus.MISSING_EVIDENCE,
            severity=MaipValidationSeverity.HIGH,
            message=(
                "The package does not provide enough numeric evidence to compare "
                "proposed MAIP against casing pressure rating."
            ),
            recommended_action=(
                "Reviewer should confirm proposed MAIP and casing pressure rating."
            ),
            supporting_values=available_values(proposed_maip, casing_rating),
        )

    if float(proposed_maip.value) >= float(casing_rating.value):
        return MaipValidationFinding(
            finding_id="maip_below_casing_pressure_rating",
            status=MaipValidationStatus.FAIL,
            severity=MaipValidationSeverity.CRITICAL,
            message="The proposed MAIP is not below the cited casing pressure rating.",
            recommended_action=(
                "Reviewer should require reconciliation between well construction "
                "pressure rating and proposed operating pressure."
            ),
            supporting_values=available_values(proposed_maip, casing_rating),
        )

    return MaipValidationFinding(
        finding_id="maip_below_casing_pressure_rating",
        status=MaipValidationStatus.PASS,
        severity=MaipValidationSeverity.INFO,
        message="The proposed MAIP is below the cited casing pressure rating.",
        recommended_action=(
            "Reviewer should confirm the casing rating, units, and source evidence."
        ),
        supporting_values=available_values(proposed_maip, casing_rating),
    )


def validate_annulus_management_evidence(
    validation_input: MaipValidationInput,
) -> MaipValidationFinding:
    """Validate that annulus pressure management evidence is present."""
    if (
        validation_input.annulus_management_evidence is None
        and validation_input.annulus_pressure_limit is None
    ):
        return MaipValidationFinding(
            finding_id="annulus_management_evidence_present",
            status=MaipValidationStatus.WARNING,
            severity=MaipValidationSeverity.MODERATE,
            message=(
                "The package does not provide clear annulus pressure management "
                "evidence linked to MAIP operations."
            ),
            recommended_action=(
                "Reviewer should confirm annulus pressure monitoring, annulus "
                "management, or response procedures."
            ),
            supporting_values=[],
        )

    return MaipValidationFinding(
        finding_id="annulus_management_evidence_present",
        status=MaipValidationStatus.PASS,
        severity=MaipValidationSeverity.INFO,
        message="Annulus pressure management evidence is present.",
        recommended_action=(
            "Reviewer should confirm the annulus evidence is linked to MAIP operations."
        ),
        supporting_values=available_values(
            validation_input.annulus_management_evidence,
            validation_input.annulus_pressure_limit,
        ),
    )


def validate_operating_margin_evidence(
    validation_input: MaipValidationInput,
) -> MaipValidationFinding:
    """Validate that operating margin evidence is present."""
    if (
        validation_input.operating_margin_evidence is None
        and validation_input.operating_pressure_limit is None
    ):
        return MaipValidationFinding(
            finding_id="operating_margin_evidence_present",
            status=MaipValidationStatus.WARNING,
            severity=MaipValidationSeverity.MODERATE,
            message=(
                "The package does not clearly document the operating margin "
                "between proposed injection pressure and the limiting pressure condition."
            ),
            recommended_action=(
                "Reviewer should confirm operating margin evidence in the operating "
                "or testing and monitoring plan."
            ),
            supporting_values=[],
        )

    return MaipValidationFinding(
        finding_id="operating_margin_evidence_present",
        status=MaipValidationStatus.PASS,
        severity=MaipValidationSeverity.INFO,
        message="Operating margin evidence is present.",
        recommended_action=(
            "Reviewer should confirm the operating margin is technically supported."
        ),
        supporting_values=available_values(
            validation_input.operating_margin_evidence,
            validation_input.operating_pressure_limit,
        ),
    )


def determine_maip_overall_status(
    findings: list[MaipValidationFinding],
) -> MaipValidationStatus:
    """Return overall MAIP validation status from individual findings."""
    if any(finding.status == MaipValidationStatus.FAIL for finding in findings):
        return MaipValidationStatus.FAIL

    if any(
        finding.status == MaipValidationStatus.MISSING_EVIDENCE
        for finding in findings
    ):
        return MaipValidationStatus.MISSING_EVIDENCE

    if any(finding.status == MaipValidationStatus.WARNING for finding in findings):
        return MaipValidationStatus.WARNING

    return MaipValidationStatus.PASS


def build_maip_summary(findings: list[MaipValidationFinding]) -> str:
    """Build a concise reviewer-facing MAIP validation summary."""
    counts = {
        MaipValidationStatus.PASS: 0,
        MaipValidationStatus.WARNING: 0,
        MaipValidationStatus.FAIL: 0,
        MaipValidationStatus.MISSING_EVIDENCE: 0,
    }

    for finding in findings:
        counts[finding.status] += 1

    if counts[MaipValidationStatus.FAIL]:
        next_step = "Resolve failed MAIP consistency checks first."
    elif counts[MaipValidationStatus.MISSING_EVIDENCE]:
        next_step = "Locate or request missing MAIP validation evidence."
    elif counts[MaipValidationStatus.WARNING]:
        next_step = "Review warning items and confirm operating margins."
    else:
        next_step = "Confirm cited evidence and proceed with reviewer sign-off."

    return (
        "MAIP validation complete. "
        f"Pass: {counts[MaipValidationStatus.PASS]}; "
        f"Warnings: {counts[MaipValidationStatus.WARNING]}; "
        f"Failures: {counts[MaipValidationStatus.FAIL]}; "
        f"Missing evidence: {counts[MaipValidationStatus.MISSING_EVIDENCE]}. "
        f"Next step: {next_step}"
    )

PRESSURE_VALUE_PATTERN = re.compile(
    r"(?P<value>\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*"
    r"(?P<unit>psi|psig|pounds per square inch)\b",
    re.IGNORECASE,
)

MAIP_CONCEPT_TERMS = {
    "proposed_maip": [
        "maip",
        "maximum allowable injection pressure",
        "maximum injection pressure",
        "injection pressure limit",
        "operating pressure limit",
    ],
    "fracture_pressure": [
        "fracture pressure",
        "formation fracture pressure",
        "fracturing pressure",
        "parting pressure",
    ],
    "fracture_gradient": [
        "fracture gradient",
    ],
    "aor_model_max_pressure": [
        "aor model pressure",
        "model pressure",
        "pressure front",
        "maximum modeled pressure",
        "maximum pressure represented",
    ],
    "casing_pressure_rating": [
        "casing pressure rating",
        "casing rating",
        "burst rating",
        "pressure rating",
    ],
    "annulus_pressure_limit": [
        "annulus pressure",
        "annular pressure",
        "annulus pressure limit",
    ],
    "operating_pressure_limit": [
        "operating pressure",
        "operating pressure limit",
        "injection pressure limit",
    ],
}

MAIP_TEXT_EVIDENCE_TERMS = {
    "annulus_management_evidence": [
        "annulus pressure",
        "annular pressure",
        "annulus monitoring",
        "annulus management",
        "annular fluid",
    ],
    "operating_margin_evidence": [
        "operating margin",
        "pressure margin",
        "safety margin",
        "below fracture pressure",
        "below the fracture pressure",
        "below maip",
    ],
}


def normalize_maip_text(value: str) -> str:
    """Normalize text for conservative MAIP evidence matching."""
    return " ".join(str(value or "").lower().replace("-", " ").split())


NEGATED_CONCEPT_PHRASES = [
    "does not identify",
    "does not provide",
    "does not document",
    "does not list",
    "not identify",
    "not provide",
    "not document",
    "not list",
    "no clear",
    "no proposed",
    "without identifying",
    "without documenting",
]


def maip_text_contains_any(text: str, terms: list[str]) -> bool:
    """Return whether text contains any non-negated normalized concept term."""
    normalized_text = normalize_maip_text(text)

    for term in terms:
        normalized_term = normalize_maip_text(term)

        if not normalized_term:
            continue

        search_start = 0

        while True:
            term_index = normalized_text.find(normalized_term, search_start)

            if term_index < 0:
                break

            context_start = max(term_index - 80, 0)
            context_end = min(
                term_index + len(normalized_term) + 40,
                len(normalized_text),
            )
            context = normalized_text[context_start:context_end]

            is_negated = any(
                phrase in context
                for phrase in NEGATED_CONCEPT_PHRASES
            )

            if not is_negated:
                return True

            search_start = term_index + len(normalized_term)

    return False

def first_non_negated_maip_term(text: str, terms: list[str]) -> str:
    """Return the first non-negated MAIP concept term found in text."""
    normalized_text = normalize_maip_text(text)

    for term in terms:
        normalized_term = normalize_maip_text(term)

        if not normalized_term:
            continue

        search_start = 0

        while True:
            term_index = normalized_text.find(normalized_term, search_start)

            if term_index < 0:
                break

            context_start = max(term_index - 80, 0)
            context_end = min(
                term_index + len(normalized_term) + 40,
                len(normalized_text),
            )
            context = normalized_text[context_start:context_end]

            is_negated = any(
                phrase in context
                for phrase in NEGATED_CONCEPT_PHRASES
            )

            if not is_negated:
                return term

            search_start = term_index + len(normalized_term)

    return ""

def parse_pressure_value(text: str) -> tuple[float, str] | None:
    """Return the first clear pressure value from text."""
    match = PRESSURE_VALUE_PATTERN.search(str(text or ""))

    if not match:
        return None

    raw_value = match.group("value").replace(",", "")

    try:
        numeric_value = float(raw_value)
    except ValueError:
        return None

    unit = match.group("unit").lower()

    if unit == "pounds per square inch":
        unit = "psi"

    return numeric_value, unit


def finding_candidate_text(finding: dict) -> str:
    """Collect reviewer-facing text fields from one finding."""
    parts = [
        finding.get("item_id", ""),
        finding.get("label", ""),
        finding.get("finding", ""),
        finding.get("recommended_fix", ""),
    ]

    parts.extend(finding.get("matched_terms", []) or [])
    parts.extend(finding.get("supporting_excerpts", []) or [])

    for location in finding.get("evidence_locations", []) or []:
        parts.append(location.get("excerpt", ""))

    return "\n".join(str(part or "") for part in parts)


def first_finding_location(finding: dict) -> dict:
    """Return first evidence location for a finding, if available."""
    locations = finding.get("evidence_locations", []) or []

    if not locations:
        return {}

    return locations[0] or {}


def maip_evidence_value_from_finding(
    *,
    concept: str,
    finding: dict,
    document_name: str,
) -> MaipEvidenceValue | None:
    """Extract one conservative MAIP evidence value from a finding."""
    text = finding_candidate_text(finding)
    concept_terms = MAIP_CONCEPT_TERMS.get(concept, [])

    if not maip_text_contains_any(text, concept_terms):
        return None

    parsed_pressure = parse_pressure_value(text)

    if parsed_pressure is None:
        return None

    numeric_value, unit = parsed_pressure
    location = first_finding_location(finding)

    matched_term = first_non_negated_maip_term(text, concept_terms)

    return MaipEvidenceValue(
        concept=concept,
        value=numeric_value,
        unit=unit,
        source_file=location.get("file_name") or document_name,
        page_number=location.get("page_number"),
        excerpt=location.get("excerpt") or (finding.get("supporting_excerpts", []) or [""])[0],
        confidence=finding.get("confidence", "Low"),
        source_finding_id=finding.get("item_id", ""),
        source_label=finding.get("label", ""),
        matched_term=matched_term,
        extraction_method="concept_term_plus_pressure_value",
        extraction_notes=(
            "Extracted because a MAIP-related concept term and a clear pressure "
            "value appeared in the same checklist finding or evidence excerpt."
        ),
    )


def maip_text_evidence_from_finding(
    *,
    concept: str,
    finding: dict,
    document_name: str,
) -> MaipEvidenceValue | None:
    """Extract non-numeric MAIP supporting evidence from a finding."""
    text = finding_candidate_text(finding)
    concept_terms = MAIP_TEXT_EVIDENCE_TERMS.get(concept, [])

    if not maip_text_contains_any(text, concept_terms):
        return None

    location = first_finding_location(finding)

    matched_term = first_non_negated_maip_term(text, concept_terms)

    return MaipEvidenceValue(
        concept=concept,
        value=None,
        unit="",
        source_file=location.get("file_name") or document_name,
        page_number=location.get("page_number"),
        excerpt=location.get("excerpt") or (finding.get("supporting_excerpts", []) or [""])[0],
        confidence=finding.get("confidence", "Low"),
        source_finding_id=finding.get("item_id", ""),
        source_label=finding.get("label", ""),
        matched_term=matched_term,
        extraction_method="concept_term_text_evidence",
        extraction_notes=(
            "Extracted as non-numeric supporting evidence because a MAIP-related "
            "concept term appeared in the checklist finding or evidence excerpt."
        ),
    )


def collect_package_review_findings(
    document_reviews: list[dict],
) -> list[tuple[str, dict]]:
    """Collect findings from package document review dictionaries."""
    collected: list[tuple[str, dict]] = []

    for document_review in document_reviews:
        document_name = document_review.get("document_name", "Unknown document")
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
                collected.append((document_name, finding))

    return collected


def choose_first_maip_value(
    values: list[MaipEvidenceValue],
) -> MaipEvidenceValue | None:
    """Return the first extracted value, preserving deterministic order."""
    return values[0] if values else None


def build_maip_validation_input_from_package_reviews(
    document_reviews: list[dict],
) -> MaipValidationInput:
    """Build MAIP validation input from package review findings.

    This extraction is intentionally conservative. It only creates structured
    values when a concept term and a clear pressure value appear in the same
    finding text/evidence.
    """
    numeric_values: dict[str, list[MaipEvidenceValue]] = {
        concept: []
        for concept in MAIP_CONCEPT_TERMS
    }
    text_values: dict[str, list[MaipEvidenceValue]] = {
        concept: []
        for concept in MAIP_TEXT_EVIDENCE_TERMS
    }

    for document_name, finding in collect_package_review_findings(document_reviews):
        for concept in MAIP_CONCEPT_TERMS:
            value = maip_evidence_value_from_finding(
                concept=concept,
                finding=finding,
                document_name=document_name,
            )

            if value is not None:
                numeric_values[concept].append(value)

        for concept in MAIP_TEXT_EVIDENCE_TERMS:
            value = maip_text_evidence_from_finding(
                concept=concept,
                finding=finding,
                document_name=document_name,
            )

            if value is not None:
                text_values[concept].append(value)

    return MaipValidationInput(
        proposed_maip=choose_first_maip_value(numeric_values["proposed_maip"]),
        fracture_pressure=choose_first_maip_value(numeric_values["fracture_pressure"]),
        fracture_gradient=choose_first_maip_value(numeric_values["fracture_gradient"]),
        aor_model_max_pressure=choose_first_maip_value(
            numeric_values["aor_model_max_pressure"]
        ),
        casing_pressure_rating=choose_first_maip_value(
            numeric_values["casing_pressure_rating"]
        ),
        annulus_pressure_limit=choose_first_maip_value(
            numeric_values["annulus_pressure_limit"]
        ),
        operating_pressure_limit=choose_first_maip_value(
            numeric_values["operating_pressure_limit"]
        ),
        annulus_management_evidence=choose_first_maip_value(
            text_values["annulus_management_evidence"]
        ),
        operating_margin_evidence=choose_first_maip_value(
            text_values["operating_margin_evidence"]
        ),
    )

def validate_maip_chain(
    validation_input: MaipValidationInput,
) -> MaipValidationReport:
    """Run all deterministic MAIP validation checks."""
    findings = [
        validate_maip_evidence_present(validation_input),
        validate_fracture_pressure_evidence_present(validation_input),
        validate_maip_below_fracture_pressure_limit(validation_input),
        validate_maip_within_aor_model_pressure(validation_input),
        validate_maip_below_casing_rating(validation_input),
        validate_annulus_management_evidence(validation_input),
        validate_operating_margin_evidence(validation_input),
    ]

    return MaipValidationReport(
        overall_status=determine_maip_overall_status(findings),
        summary=build_maip_summary(findings),
        findings=findings,
    )