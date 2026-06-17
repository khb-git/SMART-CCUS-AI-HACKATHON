"""Deterministic MAIP demo package fixture.

This module builds a small in-memory package review response that exercises the
MAIP workflow without requiring uploaded files, RAG, or an LLM.

Architecture:
    Backend decides.
    Reviewer confirms.
    LLM explains.
"""

from __future__ import annotations

from typing import Any

from review.maip_validation import (
    build_maip_validation_input_from_package_reviews,
    validate_maip_chain,
)
from review.report_export import (
    build_final_review_packet,
    build_markdown_package_report,
)


def demo_finding(
    *,
    item_id: str,
    label: str,
    text: str,
    document_name: str,
    page_number: int,
    status: str = "evidence_found",
    severity: str = "moderate",
    confidence: str = "Medium",
) -> dict[str, Any]:
    """Build one deterministic checklist finding for the MAIP demo."""
    return {
        "item_id": item_id,
        "label": label,
        "status": status,
        "severity": severity,
        "requirement_level": "required",
        "finding": text,
        "recommended_fix": "Reviewer should confirm the cited source and pressure basis.",
        "matched_terms": [],
        "supporting_excerpts": [text],
        "confidence": confidence,
        "evidence_locations": [
            {
                "file_name": document_name,
                "page_number": page_number,
                "excerpt": text,
            }
        ],
    }


def demo_document_review(
    *,
    document_name: str,
    document_type: str,
    findings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build one deterministic package document review for the MAIP demo."""
    return {
        "document_name": document_name,
        "document_type": document_type,
        "classification_confidence": "High",
        "classification": {
            "selected_plan_type": document_type,
            "confidence": "High",
        },
        "covered_plan_types": [document_type],
        "coverage_plan_types": [document_type],
        "is_combined_document": False,
        "document_role": "main",
        "supporting_document_type": "",
        "report": None,
        "checklist_reports": {
            document_type: {
                "overall_status": "mostly_complete",
                "summary": f"Demo checklist report for {document_type}.",
                "findings": findings,
            }
        },
        "error": "",
    }


def build_maip_demo_document_reviews() -> list[dict[str, Any]]:
    """Return deterministic document reviews that exercise MAIP extraction."""
    return [
        demo_document_review(
            document_name="Demo_Site_Operating_Plan.pdf",
            document_type="site_operating",
            findings=[
                demo_finding(
                    item_id="maximum_allowable_injection_pressure",
                    label="Maximum allowable injection pressure",
                    text=(
                        "The proposed MAIP is 1,800 psi for injection operations. "
                        "The operating plan documents a reviewer-checkable injection "
                        "pressure basis."
                    ),
                    document_name="Demo_Site_Operating_Plan.pdf",
                    page_number=8,
                    severity="critical",
                    confidence="High",
                ),
                demo_finding(
                    item_id="operating_margin",
                    label="Operating margin",
                    text=(
                        "The operating margin remains below fracture pressure during "
                        "normal injection operations."
                    ),
                    document_name="Demo_Site_Operating_Plan.pdf",
                    page_number=9,
                    status="present",
                    severity="moderate",
                    confidence="Medium",
                ),
            ],
        ),
        demo_document_review(
            document_name="Demo_Geologic_Characterization.pdf",
            document_type="site_geologic_characterization",
            findings=[
                demo_finding(
                    item_id="fracture_pressure",
                    label="Fracture pressure",
                    text="The formation fracture pressure is 2,200 psi.",
                    document_name="Demo_Geologic_Characterization.pdf",
                    page_number=14,
                    severity="critical",
                    confidence="High",
                ),
            ],
        ),
        demo_document_review(
            document_name="Demo_AoR_Model.pdf",
            document_type="aor_corrective_action",
            findings=[
                demo_finding(
                    item_id="aor_model_pressure",
                    label="AoR model pressure",
                    text=(
                        "The AoR model pressure assumption uses a maximum modeled "
                        "pressure of 2,000 psi."
                    ),
                    document_name="Demo_AoR_Model.pdf",
                    page_number=22,
                    severity="critical",
                    confidence="High",
                ),
            ],
        ),
        demo_document_review(
            document_name="Demo_Well_Construction.pdf",
            document_type="well_construction",
            findings=[
                demo_finding(
                    item_id="casing_pressure_rating",
                    label="Casing pressure rating",
                    text="The casing pressure rating is 3,000 psi.",
                    document_name="Demo_Well_Construction.pdf",
                    page_number=5,
                    severity="critical",
                    confidence="High",
                ),
            ],
        ),
        demo_document_review(
            document_name="Demo_Testing_Monitoring.pdf",
            document_type="testing_monitoring",
            findings=[
                demo_finding(
                    item_id="annulus_pressure_monitoring",
                    label="Annulus pressure monitoring",
                    text="Annulus pressure will be monitored continuously during injection.",
                    document_name="Demo_Testing_Monitoring.pdf",
                    page_number=11,
                    status="present",
                    severity="moderate",
                    confidence="Medium",
                ),
            ],
        ),
    ]


def build_maip_demo_package_response() -> dict[str, Any]:
    """Build a deterministic package response for the MAIP demo."""
    document_reviews = build_maip_demo_document_reviews()
    validation_input = build_maip_validation_input_from_package_reviews(
        document_reviews
    )
    maip_validation = validate_maip_chain(validation_input)

    return {
        "package_name": "maip_demo_package",
        "storage_policy": "Demo fixture only. No uploaded files are processed.",
        "report": {
            "package_name": "maip_demo_package",
            "overall_status": "needs_review",
            "summary": (
                "Deterministic demo package showing MAIP extraction, validation, "
                "audit trail, and export behavior."
            ),
            "expected_plan_types": [
                "project_narrative",
                "aor_corrective_action",
                "financial_responsibility",
                "well_construction",
                "testing_monitoring",
                "injection_well_plugging",
                "pisc_site_closure",
                "emergency_remedial_response",
            ],
            "required_plan_types": [
                "project_narrative",
                "aor_corrective_action",
                "financial_responsibility",
                "well_construction",
                "testing_monitoring",
                "injection_well_plugging",
                "pisc_site_closure",
                "emergency_remedial_response",
            ],
            "detected_plan_types": [
                "site_operating",
                "site_geologic_characterization",
                "aor_corrective_action",
                "well_construction",
                "testing_monitoring",
            ],
            "missing_required_plan_types": [
                "project_narrative",
                "financial_responsibility",
                "injection_well_plugging",
                "pisc_site_closure",
                "emergency_remedial_response",
            ],
            "missing_expected_plan_types": [
                "project_narrative",
                "financial_responsibility",
                "injection_well_plugging",
                "pisc_site_closure",
                "emergency_remedial_response",
            ],
            "duplicate_plan_types": [],
            "unknown_documents": [],
            "supporting_documents": [],
            "coverage_evidence": [],
            "document_reviews": document_reviews,
            "maip_validation": maip_validation.to_dict(),
        },
    }


def build_maip_demo_markdown_report() -> str:
    """Build the MAIP demo package Markdown report."""
    return build_markdown_package_report(build_maip_demo_package_response())


def build_maip_demo_final_review_packet() -> str:
    """Build the MAIP demo final review packet."""
    return build_final_review_packet(build_maip_demo_package_response())


if __name__ == "__main__":
    print(build_maip_demo_final_review_packet())