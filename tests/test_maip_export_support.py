from review.maip_validation import (
    MaipEvidenceValue,
    MaipValidationInput,
    validate_maip_chain,
)
from review.report_export import (
    build_final_review_packet,
    build_maip_validation_section,
    build_markdown_package_report,
    format_maip_audit_trail,
    format_maip_supporting_value,
)


def package_response_with_maip_validation():
    maip_validation = validate_maip_chain(MaipValidationInput()).to_dict()

    return {
        "package_name": "test_package",
        "storage_policy": "Uploaded files are processed temporarily.",
        "report": {
            "package_name": "test_package",
            "overall_status": "needs_review",
            "summary": "Package review complete.",
            "expected_plan_types": [],
            "required_plan_types": [],
            "detected_plan_types": [],
            "missing_required_plan_types": [],
            "missing_expected_plan_types": [],
            "duplicate_plan_types": [],
            "unknown_documents": [],
            "supporting_documents": [],
            "coverage_evidence": [],
            "document_reviews": [],
            "maip_validation": maip_validation,
        },
    }


def test_build_maip_validation_section_includes_conservative_findings():
    report = package_response_with_maip_validation()["report"]

    section = "\n".join(build_maip_validation_section(report))

    assert "## MAIP Cross-Reference Validation" in section
    assert "Overall MAIP status" in section
    assert "Missing Evidence" in section
    assert "maip_evidence_present" in section
    assert "fracture_pressure_evidence_present" in section
    assert "missing evidence rather than inferring values" in section


def test_markdown_package_report_includes_maip_validation_section():
    markdown = build_markdown_package_report(package_response_with_maip_validation())

    assert "## MAIP Cross-Reference Validation" in markdown
    assert "maip_evidence_present" in markdown
    assert "fracture_pressure_evidence_present" in markdown


def test_final_review_packet_includes_maip_validation_section():
    markdown = build_final_review_packet(package_response_with_maip_validation())

    assert "# Class VI Final Review Packet" in markdown
    assert "## MAIP Cross-Reference Validation" in markdown
    assert "maip_evidence_present" in markdown
    assert "fracture_pressure_evidence_present" in markdown


def test_maip_validation_section_handles_missing_report_for_compatibility():
    section = "\n".join(build_maip_validation_section({}))

    assert "## MAIP Cross-Reference Validation" in section
    assert "No MAIP validation report was returned." in section

def test_format_maip_supporting_value_includes_source_location():
    value = {
        "concept": "proposed_maip",
        "value": 1800.0,
        "unit": "psi",
        "source_file": "Operating_Plan.pdf",
        "page_number": 8,
    }

    assert (
        format_maip_supporting_value(value)
        == "proposed_maip: 1800.0 psi (Operating_Plan.pdf, page 8)"
    )


def test_format_maip_audit_trail_includes_extraction_metadata():
    value = {
        "concept": "proposed_maip",
        "source_finding_id": "maximum_allowable_injection_pressure",
        "source_label": "Maximum allowable injection pressure",
        "matched_term": "maip",
        "extraction_method": "concept_term_plus_pressure_value",
        "confidence": "Medium",
        "extraction_notes": "Extracted from checklist finding.",
    }

    audit_text = format_maip_audit_trail(value)

    assert "concept=proposed_maip" in audit_text
    assert "finding_id=maximum_allowable_injection_pressure" in audit_text
    assert "label=Maximum allowable injection pressure" in audit_text
    assert "matched_term=maip" in audit_text
    assert "method=concept_term_plus_pressure_value" in audit_text
    assert "confidence=Medium" in audit_text
    assert "notes=Extracted from checklist finding." in audit_text


def test_maip_validation_section_includes_audit_trail_column():
    report = package_response_with_maip_validation()["report"]
    report["maip_validation"]["findings"][0]["supporting_values"] = [
        MaipEvidenceValue(
            concept="proposed_maip",
            value=1800.0,
            unit="psi",
            source_file="Operating_Plan.pdf",
            page_number=8,
            confidence="Medium",
            source_finding_id="maximum_allowable_injection_pressure",
            source_label="Maximum allowable injection pressure",
            matched_term="maip",
            extraction_method="concept_term_plus_pressure_value",
            extraction_notes="Extracted from checklist finding.",
        ).to_dict()
    ]

    section = "\n".join(build_maip_validation_section(report))

    assert "| Status | Severity | Finding | Message | Recommended Action | Supporting Values | Audit Trail |" in section
    assert "proposed_maip: 1800.0 psi (Operating_Plan.pdf, page 8)" in section
    assert "finding_id=maximum_allowable_injection_pressure" in section
    assert "matched_term=maip" in section
    assert "method=concept_term_plus_pressure_value" in section