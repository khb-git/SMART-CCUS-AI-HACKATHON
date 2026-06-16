"""Deterministic MAIP cross-reference validation.

This module validates Maximum Allowable Injection Pressure evidence from
structured inputs. It does not use an LLM, RAG, or broad numeric extraction.

Architecture:
    Backend decides.
    Reviewer confirms.
    LLM explains.
"""

from __future__ import annotations

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