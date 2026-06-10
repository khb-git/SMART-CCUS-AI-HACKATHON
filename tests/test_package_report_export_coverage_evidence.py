def test_package_markdown_export_includes_coverage_evidence_section():
    from review.report_export import build_markdown_package_report

    package_response = {
        "package_name": "demo_package",
        "storage_policy": "Uploaded review files are temporary.",
        "report": {
            "package_name": "demo_package",
            "overall_status": "package_review_ready",
            "summary": "Package review complete.",
            "expected_plan_types": ["project_narrative", "financial_responsibility"],
            "required_plan_types": ["project_narrative", "financial_responsibility"],
            "detected_plan_types": ["project_narrative", "financial_responsibility"],
            "missing_required_plan_types": [],
            "missing_expected_plan_types": [],
            "duplicate_plan_types": [],
            "unknown_documents": [],
            "supporting_documents": [],
            "coverage_evidence": [
                {
                    "plan_type": "financial_responsibility",
                    "document_name": "Project_Narrative.pdf",
                    "document_type": "project_narrative",
                    "evidence_source": "text_evidence",
                    "matched_terms": [
                        "financial assurance",
                        "cost estimate",
                        "plugging cost",
                    ],
                    "note": "Relevant text evidence found; reviewer confirmation recommended.",
                }
            ],
            "document_reviews": [],
        },
    }

    markdown = build_markdown_package_report(package_response)

    assert "## Package Coverage Evidence" in markdown
    assert "This section explains why package topics were credited as detected." in markdown
    assert "| Package topic | Document | Primary type | Evidence source | Matched terms | Note |" in markdown
    assert "`financial_responsibility`" in markdown
    assert "`Project_Narrative.pdf`" in markdown
    assert "text_evidence" in markdown
    assert "`financial assurance`" in markdown
    assert "reviewer confirmation recommended" in markdown


def test_package_markdown_export_handles_missing_coverage_evidence():
    from review.report_export import build_markdown_package_report

    package_response = {
        "package_name": "demo_package",
        "report": {
            "package_name": "demo_package",
            "overall_status": "missing_required_documents",
            "summary": "Package review complete.",
            "expected_plan_types": [],
            "required_plan_types": [],
            "detected_plan_types": [],
            "missing_required_plan_types": [],
            "missing_expected_plan_types": [],
            "duplicate_plan_types": [],
            "unknown_documents": [],
            "supporting_documents": [],
            "document_reviews": [],
        },
    }

    markdown = build_markdown_package_report(package_response)

    assert "## Package Coverage Evidence" in markdown
    assert "No package coverage evidence was returned." in markdown