from review.maip_validation import (
    MaipValidationStatus,
    build_maip_validation_input_from_package_reviews,
    validate_maip_chain,
)
from review.package_review import (
    PackageDocumentReview,
    build_package_maip_validation_report,
)


def finding(
    *,
    item_id: str,
    label: str,
    text: str,
    document_name: str,
    page_number: int,
) -> dict:
    return {
        "item_id": item_id,
        "label": label,
        "status": "evidence_found",
        "severity": "moderate",
        "requirement_level": "required",
        "finding": text,
        "matched_terms": [],
        "supporting_excerpts": [text],
        "confidence": "Medium",
        "evidence_locations": [
            {
                "file_name": document_name,
                "page_number": page_number,
                "excerpt": text,
            }
        ],
    }


def package_document_review(
    *,
    document_name: str,
    document_type: str,
    findings: list[dict],
) -> dict:
    return {
        "document_name": document_name,
        "document_type": document_type,
        "classification_confidence": "High",
        "classification": {},
        "checklist_reports": {
            document_type: {
                "findings": findings,
            }
        },
    }


def test_build_maip_validation_input_extracts_clear_pressure_values():
    document_reviews = [
        package_document_review(
            document_name="Operating_Plan.pdf",
            document_type="site_operating",
            findings=[
                finding(
                    item_id="maximum_allowable_injection_pressure",
                    label="Maximum allowable injection pressure",
                    text="The proposed MAIP is 1,800 psi for injection operations.",
                    document_name="Operating_Plan.pdf",
                    page_number=8,
                ),
                finding(
                    item_id="operating_margin",
                    label="Operating margin",
                    text="The operating margin remains below the fracture pressure limit.",
                    document_name="Operating_Plan.pdf",
                    page_number=9,
                ),
            ],
        ),
        package_document_review(
            document_name="Geologic_Characterization.pdf",
            document_type="site_geologic_characterization",
            findings=[
                finding(
                    item_id="fracture_pressure",
                    label="Fracture pressure",
                    text="The formation fracture pressure is 2,200 psi.",
                    document_name="Geologic_Characterization.pdf",
                    page_number=14,
                ),
            ],
        ),
        package_document_review(
            document_name="AoR_Model.pdf",
            document_type="aor_corrective_action",
            findings=[
                finding(
                    item_id="aor_model_pressure",
                    label="AoR model pressure",
                    text="The AoR model pressure assumption uses a maximum modeled pressure of 2,000 psi.",
                    document_name="AoR_Model.pdf",
                    page_number=22,
                ),
            ],
        ),
        package_document_review(
            document_name="Well_Construction.pdf",
            document_type="well_construction",
            findings=[
                finding(
                    item_id="casing_pressure_rating",
                    label="Casing pressure rating",
                    text="The casing pressure rating is 3,000 psi.",
                    document_name="Well_Construction.pdf",
                    page_number=5,
                ),
            ],
        ),
        package_document_review(
            document_name="Testing_Monitoring.pdf",
            document_type="testing_monitoring",
            findings=[
                finding(
                    item_id="annulus_pressure_monitoring",
                    label="Annulus pressure monitoring",
                    text="Annulus pressure will be monitored continuously during injection.",
                    document_name="Testing_Monitoring.pdf",
                    page_number=11,
                ),
            ],
        ),
    ]

    validation_input = build_maip_validation_input_from_package_reviews(document_reviews)

    assert validation_input.proposed_maip.value == 1800.0
    assert validation_input.proposed_maip.source_file == "Operating_Plan.pdf"
    assert validation_input.proposed_maip.page_number == 8

    assert validation_input.fracture_pressure.value == 2200.0
    assert validation_input.aor_model_max_pressure.value == 2000.0
    assert validation_input.casing_pressure_rating.value == 3000.0
    assert validation_input.annulus_management_evidence is not None
    assert validation_input.operating_margin_evidence is not None


def test_validate_maip_chain_passes_when_extracted_values_are_consistent():
    document_reviews = [
        package_document_review(
            document_name="Operating_Plan.pdf",
            document_type="site_operating",
            findings=[
                finding(
                    item_id="maximum_allowable_injection_pressure",
                    label="Maximum allowable injection pressure",
                    text="The proposed MAIP is 1,800 psi.",
                    document_name="Operating_Plan.pdf",
                    page_number=8,
                ),
                finding(
                    item_id="operating_margin",
                    label="Operating margin",
                    text="The operating margin remains below fracture pressure.",
                    document_name="Operating_Plan.pdf",
                    page_number=9,
                ),
            ],
        ),
        package_document_review(
            document_name="Geologic_Characterization.pdf",
            document_type="site_geologic_characterization",
            findings=[
                finding(
                    item_id="fracture_pressure",
                    label="Fracture pressure",
                    text="The fracture pressure is 2,200 psi.",
                    document_name="Geologic_Characterization.pdf",
                    page_number=14,
                ),
            ],
        ),
        package_document_review(
            document_name="AoR_Model.pdf",
            document_type="aor_corrective_action",
            findings=[
                finding(
                    item_id="aor_model_pressure",
                    label="AoR model pressure",
                    text="The AoR model pressure assumption is 2,000 psi.",
                    document_name="AoR_Model.pdf",
                    page_number=22,
                ),
            ],
        ),
        package_document_review(
            document_name="Well_Construction.pdf",
            document_type="well_construction",
            findings=[
                finding(
                    item_id="casing_pressure_rating",
                    label="Casing pressure rating",
                    text="The casing pressure rating is 3,000 psi.",
                    document_name="Well_Construction.pdf",
                    page_number=5,
                ),
            ],
        ),
        package_document_review(
            document_name="Testing_Monitoring.pdf",
            document_type="testing_monitoring",
            findings=[
                finding(
                    item_id="annulus_pressure_monitoring",
                    label="Annulus pressure monitoring",
                    text="Annulus pressure will be monitored continuously.",
                    document_name="Testing_Monitoring.pdf",
                    page_number=11,
                ),
            ],
        ),
    ]

    validation_input = build_maip_validation_input_from_package_reviews(document_reviews)
    report = validate_maip_chain(validation_input)

    assert report.overall_status == MaipValidationStatus.PASS


def test_validate_maip_chain_fails_when_extracted_maip_exceeds_fracture_limit():
    document_reviews = [
        package_document_review(
            document_name="Operating_Plan.pdf",
            document_type="site_operating",
            findings=[
                finding(
                    item_id="maximum_allowable_injection_pressure",
                    label="Maximum allowable injection pressure",
                    text="The proposed MAIP is 2,050 psi.",
                    document_name="Operating_Plan.pdf",
                    page_number=8,
                ),
            ],
        ),
        package_document_review(
            document_name="Geologic_Characterization.pdf",
            document_type="site_geologic_characterization",
            findings=[
                finding(
                    item_id="fracture_pressure",
                    label="Fracture pressure",
                    text="The fracture pressure is 2,200 psi.",
                    document_name="Geologic_Characterization.pdf",
                    page_number=14,
                ),
            ],
        ),
        package_document_review(
            document_name="AoR_Model.pdf",
            document_type="aor_corrective_action",
            findings=[
                finding(
                    item_id="aor_model_pressure",
                    label="AoR model pressure",
                    text="The AoR model pressure assumption is 2,300 psi.",
                    document_name="AoR_Model.pdf",
                    page_number=22,
                ),
            ],
        ),
        package_document_review(
            document_name="Well_Construction.pdf",
            document_type="well_construction",
            findings=[
                finding(
                    item_id="casing_pressure_rating",
                    label="Casing pressure rating",
                    text="The casing pressure rating is 3,000 psi.",
                    document_name="Well_Construction.pdf",
                    page_number=5,
                ),
            ],
        ),
    ]

    validation_input = build_maip_validation_input_from_package_reviews(document_reviews)
    report = validate_maip_chain(validation_input)

    assert report.overall_status == MaipValidationStatus.FAIL

    finding_ids = {
        finding.finding_id: finding
        for finding in report.findings
    }

    assert (
        finding_ids["maip_below_90_percent_fracture_pressure"].status
        == MaipValidationStatus.FAIL
    )


def test_package_maip_validation_report_uses_extracted_document_review_values():
    document_review = PackageDocumentReview(
        document_name="Operating_Plan.pdf",
        document_type="site_operating",
        classification_confidence="High",
        classification={},
        checklist_reports={
            "site_operating": {
                "findings": [
                    finding(
                        item_id="maximum_allowable_injection_pressure",
                        label="Maximum allowable injection pressure",
                        text="The proposed MAIP is 1,800 psi.",
                        document_name="Operating_Plan.pdf",
                        page_number=8,
                    )
                ]
            }
        },
    )

    report = build_package_maip_validation_report([document_review])
    report_dict = report.to_dict()

    maip_finding = next(
        finding
        for finding in report_dict["findings"]
        if finding["finding_id"] == "maip_evidence_present"
    )

    assert maip_finding["status"] == "pass"
    assert maip_finding["supporting_values"][0]["value"] == 1800.0
    assert maip_finding["supporting_values"][0]["source_file"] == "Operating_Plan.pdf"


def test_maip_extraction_ignores_pressure_values_without_concept_terms():
    document_reviews = [
        package_document_review(
            document_name="Random_Table.pdf",
            document_type="project_narrative",
            findings=[
                finding(
                    item_id="random_pressure",
                    label="Pressure table",
                    text="A table lists 1,800 psi but does not identify MAIP or fracture pressure.",
                    document_name="Random_Table.pdf",
                    page_number=3,
                )
            ],
        )
    ]

    validation_input = build_maip_validation_input_from_package_reviews(document_reviews)

    assert validation_input.proposed_maip is None
    assert validation_input.fracture_pressure is None

def test_maip_extraction_records_audit_trail_for_numeric_value():
    document_reviews = [
        package_document_review(
            document_name="Operating_Plan.pdf",
            document_type="site_operating",
            findings=[
                finding(
                    item_id="maximum_allowable_injection_pressure",
                    label="Maximum allowable injection pressure",
                    text="The proposed MAIP is 1,800 psi for injection operations.",
                    document_name="Operating_Plan.pdf",
                    page_number=8,
                )
            ],
        )
    ]

    validation_input = build_maip_validation_input_from_package_reviews(document_reviews)
    value = validation_input.proposed_maip

    assert value.source_finding_id == "maximum_allowable_injection_pressure"
    assert value.source_label == "Maximum allowable injection pressure"
    assert value.matched_term == "maip"
    assert value.extraction_method == "concept_term_plus_pressure_value"
    assert "clear pressure value" in value.extraction_notes

    value_dict = value.to_dict()

    assert value_dict["source_finding_id"] == "maximum_allowable_injection_pressure"
    assert value_dict["matched_term"] == "maip"
    assert value_dict["extraction_method"] == "concept_term_plus_pressure_value"