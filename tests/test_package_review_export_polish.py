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

def test_markdown_package_report_includes_reviewer_priority_summary():
    from review.report_export import build_markdown_package_report

    package_response = {
        "package_name": "priority_package",
        "report": {
            "package_name": "priority_package",
            "overall_status": "missing_required_documents",
            "summary": "Package review complete.",
            "detected_plan_types": ["testing_monitoring"],
            "missing_required_plan_types": ["site_operating"],
            "missing_expected_plan_types": ["site_operating"],
            "duplicate_plan_types": [],
            "unknown_documents": [],
            "supporting_documents": ["Marquis_Alternative_PISC_Timeframe.pdf"],
            "expected_plan_types": ["testing_monitoring", "site_operating"],
            "required_plan_types": ["testing_monitoring", "site_operating"],
            "document_reviews": [
                {
                    "document_name": "Marquis_Testing_and_Monitoring_Plan.pdf",
                    "document_type": "testing_monitoring",
                    "classification_confidence": "high",
                    "classification": {},
                    "document_role": "main",
                    "supporting_document_type": "",
                    "covered_plan_types": ["testing_monitoring"],
                    "checklist_reports": {
                        "testing_monitoring": {
                            "overall_status": "needs_revision",
                            "checklist_id": "testing_monitoring_v1",
                            "summary": "Testing and monitoring review complete.",
                            "findings": [
                                {
                                    "status": "missing",
                                    "label": "Annular pressure monitoring",
                                    "item_id": "annular_pressure_monitoring",
                                    "finding": "Annular pressure monitoring was not found.",
                                    "matched_evidence_group_names": [],
                                    "recommended_fix": "Add annular pressure monitoring details.",
                                    "severity": "critical",
                                    "requirement_level": "required",
                                },
                                {
                                    "status": "evidence_found",
                                    "label": "SCADA or data recording system",
                                    "item_id": "scada_or_data_recording",
                                    "finding": "Evidence was found for reporting.",
                                    "matched_evidence_group_names": ["reporting"],
                                    "recommended_fix": "Confirm SCADA/data recording details.",
                                    "severity": "moderate",
                                    "requirement_level": "required",
                                },
                            ],
                        }
                    },
                    "report": {},
                    "error": "",
                }
            ],
        },
    }

    markdown = build_markdown_package_report(package_response)

    assert "## Reviewer Priority Summary" in markdown
    assert "**Missing required document types:**" in markdown
    assert "`site_operating`" in markdown
    assert "**Supporting documents detected:**" in markdown
    assert "Marquis_Alternative_PISC_Timeframe.pdf" in markdown
    assert "Annular pressure monitoring" in markdown
    assert "Document: `Marquis_Testing_and_Monitoring_Plan.pdf`" in markdown
    assert "Checklist: `testing_monitoring`" in markdown
    assert "Matched evidence groups: `reporting`" in markdown


def test_markdown_package_report_priority_summary_handles_clean_package():
    from review.report_export import build_markdown_package_report

    package_response = {
        "package_name": "clean_package",
        "report": {
            "package_name": "clean_package",
            "overall_status": "package_review_ready",
            "summary": "Package review complete.",
            "detected_plan_types": ["project_narrative"],
            "missing_required_plan_types": [],
            "missing_expected_plan_types": [],
            "duplicate_plan_types": [],
            "unknown_documents": [],
            "supporting_documents": [],
            "expected_plan_types": ["project_narrative"],
            "required_plan_types": ["project_narrative"],
            "document_reviews": [
                {
                    "document_name": "Narrative.pdf",
                    "document_type": "project_narrative",
                    "classification_confidence": "high",
                    "classification": {},
                    "document_role": "main",
                    "supporting_document_type": "",
                    "covered_plan_types": ["project_narrative"],
                    "checklist_reports": {
                        "project_narrative": {
                            "overall_status": "review_ready",
                            "checklist_id": "project_narrative_v1",
                            "summary": "Narrative review complete.",
                            "findings": [
                                {
                                    "status": "present",
                                    "label": "Project description",
                                    "item_id": "project_description",
                                    "finding": "Project description appears addressed.",
                                    "recommended_fix": "",
                                }
                            ],
                        }
                    },
                    "report": {},
                    "error": "",
                }
            ],
        },
    }

    markdown = build_markdown_package_report(package_response)

    assert "## Reviewer Priority Summary" in markdown
    assert "No package-level priority issues were identified" in markdown