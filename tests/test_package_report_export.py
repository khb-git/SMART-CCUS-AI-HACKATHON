def make_package_response():
    return {
        "package_name": "adm_package",
        "report": {
            "package_name": "adm_package",
            "overall_status": "missing_required_documents",
            "summary": (
                "Package review complete. Detected document types: 2; "
                "Missing required document types: 8; Missing expected document types: 9; "
                "Duplicate document types: 0; Unknown documents: 0."
            ),
            "expected_plan_types": [
                "project_narrative",
                "testing_monitoring",
                "injection_well_plugging",
            ],
            "required_plan_types": [
                "project_narrative",
                "testing_monitoring",
                "injection_well_plugging",
            ],
            "detected_plan_types": [
                "testing_monitoring",
                "injection_well_plugging",
            ],
            "missing_required_plan_types": [
                "project_narrative",
            ],
            "missing_expected_plan_types": [
                "project_narrative",
            ],
            "duplicate_plan_types": [],
            "unknown_documents": [],
            "document_reviews": [
                {
                    "document_name": "ADM_Testing_and_Monitoring_Plan.pdf",
                    "document_type": "testing_monitoring",
                    "classification_confidence": "high",
                    "classification": {
                        "document_type": "testing_monitoring",
                        "confidence": "high",
                        "matched_terms": ["testing and monitoring plan"],
                        "reason": "Matched uploaded document.",
                    },
                    "report": {
                        "document_name": "ADM_Testing_and_Monitoring_Plan.pdf",
                        "plan_type": "testing_monitoring",
                        "checklist_id": "testing_monitoring_v1",
                        "overall_status": "mostly_complete",
                        "summary": (
                            "Checklist review complete. Present: 1; "
                            "Evidence found: 10; Missing: 0; Unclear: 0."
                        ),
                        "findings": [
                            {
                                "item_id": "injection_rate_monitoring",
                                "label": "Injection rate and flow monitoring",
                                "status": "evidence_found",
                                "severity": "critical",
                                "requirement_level": "required",
                                "matched_terms": ["injection rate", "flow rate"],
                                "supporting_excerpts": [],
                                "finding": "Evidence was found for injection rate monitoring.",
                                "recommended_fix": "Add device, location, and frequency.",
                            }
                        ],
                    },
                    "error": "",
                },
                {
                    "document_name": "unknown_notes.pdf",
                    "document_type": "unknown",
                    "classification_confidence": "unknown",
                    "classification": {
                        "document_type": "unknown",
                        "confidence": "unknown",
                        "matched_terms": [],
                        "reason": "No supported document type rule matched.",
                    },
                    "report": None,
                    "error": "Document type could not be classified.",
                },
            ],
        },
        "storage_policy": (
            "Uploaded package documents are processed temporarily for this review "
            "request and are not stored in permanent data folders or Chroma collections."
        ),
    }


def test_build_markdown_package_report_contains_package_summary():
    from review.report_export import build_markdown_package_report

    markdown = build_markdown_package_report(make_package_response())

    assert "# Class VI Package Review Report" in markdown
    assert "**Package name:** adm_package" in markdown
    assert "**Overall status:** Missing Required Documents" in markdown
    assert "Detected document types: 2" in markdown
    assert "Uploaded package documents are processed temporarily" in markdown


def test_build_markdown_package_report_contains_coverage_sections():
    from review.report_export import build_markdown_package_report

    markdown = build_markdown_package_report(make_package_response())

    assert "## Detected Document Types" in markdown
    assert "`testing_monitoring`" in markdown
    assert "`injection_well_plugging`" in markdown
    assert "## Missing Required Document Types" in markdown
    assert "`project_narrative`" in markdown


def test_build_markdown_package_report_contains_document_summaries():
    from review.report_export import build_markdown_package_report

    markdown = build_markdown_package_report(make_package_response())

    assert "### ADM_Testing_and_Monitoring_Plan.pdf" in markdown
    assert "**Document review summary:**" in markdown
    assert "Evidence found: 10" in markdown
    assert "Injection rate and flow monitoring" in markdown
    assert "Recommended fix: Add device, location, and frequency." in markdown


def test_build_markdown_package_report_contains_unknown_document_errors():
    from review.report_export import build_markdown_package_report

    markdown = build_markdown_package_report(make_package_response())

    assert "### unknown_notes.pdf" in markdown
    assert "Document type could not be classified." in markdown


def test_default_package_report_filename_sanitizes_package_name():
    from review.report_export import default_package_report_filename

    assert (
        default_package_report_filename("ADM Package 01")
        == "ADM_Package_01_package_review_report.md"
    )