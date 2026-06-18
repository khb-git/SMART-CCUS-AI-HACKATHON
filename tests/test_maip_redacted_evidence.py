from review.maip_validation import (
    MaipValidationStatus,
    build_maip_validation_input_from_package_reviews,
    validate_maip_chain,
)


def test_maip_extractor_marks_redacted_pressure_evidence():
    document_reviews = [
        {
            "document_name": "Redacted_Operating_Plan.pdf",
            "checklist_reports": {
                "site_operating": {
                    "findings": [
                        {
                            "item_id": "maximum_allowable_injection_pressure",
                            "label": "Maximum allowable injection pressure",
                            "finding": (
                                "The proposed MAIP is provided in the application, "
                                "but the numeric value is redacted in the public version."
                            ),
                            "confidence": "High",
                            "matched_terms": [
                                "maximum allowable injection pressure",
                                "redacted",
                            ],
                            "supporting_excerpts": [
                                "Maximum allowable injection pressure: [REDACTED] psi."
                            ],
                            "evidence_locations": [
                                {
                                    "file_name": "Redacted_Operating_Plan.pdf",
                                    "page_number": 8,
                                    "excerpt": (
                                        "Maximum allowable injection pressure: "
                                        "[REDACTED] psi."
                                    ),
                                }
                            ],
                        }
                    ],
                }
            },
        }
    ]

    validation_input = build_maip_validation_input_from_package_reviews(
        document_reviews
    )

    assert validation_input.proposed_maip is not None
    assert validation_input.proposed_maip.value is None
    assert validation_input.proposed_maip.extraction_method == (
        "concept_term_plus_redaction_indicator"
    )
    assert "redacted" in validation_input.proposed_maip.extraction_notes.lower()

    report = validate_maip_chain(validation_input)
    report_dict = report.to_dict()

    assert report.overall_status == MaipValidationStatus.REDACTED_EVIDENCE
    assert report_dict["overall_status"] == "redacted_evidence"
    assert "Redacted evidence:" in report_dict["summary"]

    maip_finding = next(
        finding
        for finding in report_dict["findings"]
        if finding["finding_id"] == "maip_evidence_present"
    )

    assert maip_finding["status"] == "redacted_evidence"
    assert "redacted or unreadable" in maip_finding["message"]
    assert maip_finding["supporting_values"][0]["value"] is None


def test_maip_extractor_prefers_numeric_value_over_redacted_placeholder():
    document_reviews = [
        {
            "document_name": "Mixed_Operating_Plan.pdf",
            "checklist_reports": {
                "site_operating": {
                    "findings": [
                        {
                            "item_id": "maximum_allowable_injection_pressure_redacted",
                            "label": "Maximum allowable injection pressure",
                            "finding": "The proposed MAIP value is redacted.",
                            "confidence": "High",
                            "matched_terms": ["maip", "redacted"],
                            "supporting_excerpts": [
                                "MAIP: [REDACTED] psi."
                            ],
                            "evidence_locations": [
                                {
                                    "file_name": "Mixed_Operating_Plan.pdf",
                                    "page_number": 4,
                                    "excerpt": "MAIP: [REDACTED] psi.",
                                }
                            ],
                        },
                        {
                            "item_id": "maximum_allowable_injection_pressure",
                            "label": "Maximum allowable injection pressure",
                            "finding": "The proposed MAIP is 1800 psi.",
                            "confidence": "High",
                            "matched_terms": ["maip"],
                            "supporting_excerpts": [
                                "The proposed MAIP is 1800 psi."
                            ],
                            "evidence_locations": [
                                {
                                    "file_name": "Mixed_Operating_Plan.pdf",
                                    "page_number": 8,
                                    "excerpt": "The proposed MAIP is 1800 psi.",
                                }
                            ],
                        },
                    ],
                }
            },
        }
    ]

    validation_input = build_maip_validation_input_from_package_reviews(
        document_reviews
    )

    assert validation_input.proposed_maip is not None
    assert validation_input.proposed_maip.value == 1800.0
    assert validation_input.proposed_maip.page_number == 8