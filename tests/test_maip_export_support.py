from review.maip_validation import MaipValidationInput, validate_maip_chain
from review.report_export import (
    build_final_review_packet,
    build_maip_validation_section,
    build_markdown_package_report,
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