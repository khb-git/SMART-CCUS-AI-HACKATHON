def make_review_response():
    return {
        "document_name": "ADM_Testing_and_Monitoring_Plan.pdf",
        "document_type": "testing_monitoring",
        "classification_confidence": "high",
        "classification": {
            "document_type": "testing_monitoring",
            "confidence": "high",
            "matched_terms": [
                "testing and monitoring plan",
                "plume and pressure front tracking",
            ],
            "reason": "Matched uploaded document to Testing and Monitoring Plan.",
        },
        "report": {
            "document_name": "ADM_Testing_and_Monitoring_Plan.pdf",
            "plan_type": "testing_monitoring",
            "checklist_id": "testing_monitoring_v1",
            "overall_status": "mostly_complete",
            "summary": "Checklist review complete. Present: 4; Partial: 6; Missing: 1; Unclear: 0.",
            "findings": [
                {
                    "item_id": "annular_pressure_monitoring",
                    "label": "Annular pressure monitoring",
                    "status": "missing",
                    "severity": "critical",
                    "requirement_level": "required",
                    "matched_terms": [],
                    "supporting_excerpts": [],
                    "finding": "The document does not appear to address annular pressure monitoring.",
                    "recommended_fix": "Add annular pressure monitoring location, device, frequency, and response actions.",
                },
                {
                    "item_id": "injection_pressure_monitoring",
                    "label": "Injection pressure monitoring",
                    "status": "present",
                    "severity": "critical",
                    "requirement_level": "required",
                    "matched_terms": ["injection pressure", "continuous recording"],
                    "supporting_excerpts": [
                        "Continuous recording devices will monitor wellhead injection pressure."
                    ],
                    "finding": "The document appears to address injection pressure monitoring.",
                    "recommended_fix": "Add pressure monitoring details if missing.",
                },
            ],
        },
        "storage_policy": (
            "Uploaded documents are processed temporarily for this review request "
            "and are not stored in permanent data folders or Chroma collections."
        ),
    }


def test_build_markdown_review_report_contains_summary_and_findings():
    from review.report_export import build_markdown_review_report

    markdown = build_markdown_review_report(make_review_response())

    assert "# Class VI Document Review Report" in markdown
    assert "ADM_Testing_and_Monitoring_Plan.pdf" in markdown
    assert "**Overall status:** Mostly complete" in markdown
    assert "Checklist review complete" in markdown
    assert "### Missing — Annular pressure monitoring" in markdown
    assert "### Present — Injection pressure monitoring" in markdown
    assert "Uploaded documents are processed temporarily" in markdown


def test_build_markdown_review_report_counts_statuses():
    from review.report_export import build_markdown_review_report

    markdown = build_markdown_review_report(make_review_response())

    assert "**Present:** 1" in markdown
    assert "**Missing:** 1" in markdown
    assert "**Partial:** 0" in markdown
    assert "**Unclear:** 0" in markdown


def test_default_report_filename_sanitizes_document_name():
    from review.report_export import default_report_filename

    assert (
        default_report_filename("ADM Testing and Monitoring Plan.pdf")
        == "ADM_Testing_and_Monitoring_Plan_review_report.md"
    )


def test_status_label_formats_report_status():
    from review.report_export import status_label

    assert status_label("needs_revision") == "Needs revision"
    assert status_label("mostly_complete") == "Mostly complete"
    assert status_label("present") == "Present"