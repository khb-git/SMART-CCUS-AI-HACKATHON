def test_markdown_package_report_includes_supporting_documents():
    from review.report_export import build_markdown_package_report

    package_response = {
        "package_name": "marquis_package",
        "storage_policy": "Temporary processing only.",
        "report": {
            "package_name": "marquis_package",
            "overall_status": "package_review_ready",
            "summary": "Package review complete.",
            "detected_plan_types": ["pisc_site_closure"],
            "missing_required_plan_types": [],
            "missing_expected_plan_types": [],
            "duplicate_plan_types": [],
            "unknown_documents": [],
            "supporting_documents": [
                "Marquis_Alternative_PISC_Timeframe__4b09b5518eb0.pdf"
            ],
            "expected_plan_types": ["pisc_site_closure"],
            "required_plan_types": ["pisc_site_closure"],
            "document_reviews": [],
        },
    }

    markdown = build_markdown_package_report(package_response)

    assert "## Supporting Documents" in markdown
    assert "Marquis_Alternative_PISC_Timeframe__4b09b5518eb0.pdf" in markdown
    assert "**Supporting documents:** 1" in markdown


def test_markdown_package_report_includes_combined_checklist_reports():
    from review.report_export import build_markdown_package_report

    package_response = {
        "package_name": "combined_package",
        "report": {
            "package_name": "combined_package",
            "overall_status": "mostly_complete",
            "summary": "Package review complete.",
            "detected_plan_types": [
                "project_narrative",
                "aor_corrective_action",
            ],
            "missing_required_plan_types": [],
            "missing_expected_plan_types": [],
            "duplicate_plan_types": [],
            "unknown_documents": [],
            "supporting_documents": [],
            "expected_plan_types": [
                "project_narrative",
                "aor_corrective_action",
            ],
            "required_plan_types": [
                "project_narrative",
                "aor_corrective_action",
            ],
            "document_reviews": [
                {
                    "document_name": "combined.pdf",
                    "document_type": "project_narrative",
                    "classification_confidence": "high",
                    "classification": {
                        "matched_terms": ["project narrative"],
                        "reason": "Combined document detected.",
                    },
                    "document_role": "main",
                    "supporting_document_type": "",
                    "covered_plan_types": [
                        "project_narrative",
                        "aor_corrective_action",
                    ],
                    "checklist_reports": {
                        "project_narrative": {
                            "overall_status": "review_ready",
                            "checklist_id": "project_narrative_v1",
                            "summary": "Narrative review complete.",
                            "findings": [],
                        },
                        "aor_corrective_action": {
                            "overall_status": "mostly_complete",
                            "checklist_id": "aor_corrective_action_v1",
                            "summary": "AoR review complete.",
                            "findings": [
                                {
                                    "status": "evidence_found",
                                    "label": "AoR delineation",
                                    "item_id": "aor_delineation",
                                    "finding": "Evidence was found for model basis.",
                                    "matched_evidence_group_names": ["model_basis"],
                                    "recommended_fix": "Confirm AoR maps and model assumptions.",
                                }
                            ],
                        },
                    },
                    "report": {},
                    "error": "",
                }
            ],
        },
    }

    markdown = build_markdown_package_report(package_response)

    assert "**Checklist reports by covered plan type:**" in markdown
    assert "#### `project_narrative`" in markdown
    assert "#### `aor_corrective_action`" in markdown
    assert "Matched evidence groups: `model_basis`" in markdown
    assert "Confirm AoR maps and model assumptions." in markdown