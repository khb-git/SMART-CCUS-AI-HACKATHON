from demo_samples.maip_demo_package import (
    build_maip_demo_final_review_packet,
    build_maip_demo_markdown_report,
    build_maip_demo_package_response,
)


def test_maip_demo_package_response_includes_extracted_maip_values():
    package_response = build_maip_demo_package_response()
    maip_validation = package_response["report"]["maip_validation"]

    assert package_response["package_name"] == "maip_demo_package"
    assert maip_validation["overall_status"] == "pass"

    findings = {
        finding["finding_id"]: finding
        for finding in maip_validation["findings"]
    }

    maip_finding = findings["maip_evidence_present"]

    assert maip_finding["status"] == "pass"
    assert maip_finding["supporting_values"][0]["concept"] == "proposed_maip"
    assert maip_finding["supporting_values"][0]["value"] == 1800.0
    assert (
        maip_finding["supporting_values"][0]["source_file"]
        == "Demo_Site_Operating_Plan.pdf"
    )
    assert maip_finding["supporting_values"][0]["page_number"] == 8


def test_maip_demo_package_response_includes_audit_metadata():
    package_response = build_maip_demo_package_response()
    maip_validation = package_response["report"]["maip_validation"]

    maip_finding = next(
        finding
        for finding in maip_validation["findings"]
        if finding["finding_id"] == "maip_evidence_present"
    )

    supporting_value = maip_finding["supporting_values"][0]

    assert supporting_value["source_finding_id"] == "maximum_allowable_injection_pressure"
    assert supporting_value["source_label"] == "Maximum allowable injection pressure"
    assert supporting_value["matched_term"] == "maip"
    assert supporting_value["extraction_method"] == "concept_term_plus_pressure_value"


def test_maip_demo_markdown_report_includes_validation_and_audit_trail():
    markdown = build_maip_demo_markdown_report()

    assert "# Class VI Package Review Report" in markdown
    assert "## MAIP Cross-Reference Validation" in markdown
    assert "proposed_maip: 1800.0 psi" in markdown
    assert "Audit Trail" in markdown
    assert "finding_id=maximum_allowable_injection_pressure" in markdown
    assert "method=concept_term_plus_pressure_value" in markdown


def test_maip_demo_final_review_packet_includes_validation_and_audit_trail():
    markdown = build_maip_demo_final_review_packet()

    assert "# Class VI Final Review Packet" in markdown
    assert "## MAIP Cross-Reference Validation" in markdown
    assert "proposed_maip: 1800.0 psi" in markdown
    assert "Audit Trail" in markdown
    assert "finding_id=maximum_allowable_injection_pressure" in markdown