from review.report_export import build_markdown_package_report
from review.report_export import gsdt_module_folder_label

def test_package_report_includes_completeness_checklist_section():
    package_response = {
        "package_name": "uploaded_package",
        "storage_policy": "Temporary files are not retained.",
        "report": {
            "package_name": "uploaded_package",
            "overall_status": "needs_revision",
            "summary": "Package review complete.",
            "detected_plan_types": ["financial_responsibility"],
            "missing_required_plan_types": [],
            "missing_expected_plan_types": [],
            "duplicate_plan_types": [],
            "unknown_documents": [],
            "supporting_documents": [],
            "expected_plan_types": ["financial_responsibility"],
            "required_plan_types": ["financial_responsibility"],
            "coverage_evidence": [],
            "document_reviews": [
                {
                    "document_name": "ADM_Cost_Estimates.pdf",
                    "document_type": "financial_responsibility",
                    "document_role": "main",
                    "covered_plan_types": ["financial_responsibility"],
                    "checklist_reports": {
                        "financial_responsibility": {
                            "overall_status": "needs_revision",
                            "checklist_id": "financial_responsibility_v1",
                            "summary": "Checklist review complete.",
                            "findings": [
                                {
                                    "item_id": "coverage_amount",
                                    "label": "Coverage amount",
                                    "status": "evidence_found",
                                    "severity": "critical",
                                    "requirement_level": "required",
                                    "finding": "Coverage amount: evidence found.",
                                    "recommended_fix": "Add comparison to estimated costs.",
                                    "matched_evidence_group_names": ["cost_basis"],
                                    "evidence_locations": [
                                        {
                                            "file_name": "ADM_Cost_Estimates.pdf",
                                            "page_number": 4,
                                            "chunk_index": 1,
                                            "content_type": "text",
                                            "section_heading": "Cost Estimate",
                                            "excerpt": "The estimated cost basis is shown.",
                                            "matched_terms": ["cost estimate"],
                                        }
                                    ],
                                },
                                {
                                    "item_id": "financial_instrument",
                                    "label": "Financial instrument",
                                    "status": "missing",
                                    "severity": "critical",
                                    "requirement_level": "required",
                                    "finding": "Financial instrument: not found.",
                                    "recommended_fix": "Add the financial instrument type.",
                                    "matched_evidence_group_names": [],
                                    "evidence_locations": [],
                                    "related_package_evidence": [
                                        {
                                            "document_name": "ADM_Narrative.pdf",
                                            "document_type": "project_narrative",
                                            "matched_terms": ["cost estimate"],
                                        }
                                    ],
                                },
                            ],
                        }
                    },
                    "report": {},
                    "classification_confidence": "high",
                    "classification": {},
                    "error": "",
                }
            ],
        },
    }

    markdown = build_markdown_package_report(package_response)

    assert "## Completeness Checklist Review" in markdown
    assert "| Status | Required Item | GSDT Module/Folder | File Name | Page Number | Notes |" in markdown
    assert "| Evidence found | Coverage amount | Financial Responsibility | ADM_Cost_Estimates.pdf | 4 |" in markdown
    assert "| Missing | Financial instrument | Financial Responsibility | ADM_Cost_Estimates.pdf | Not found |" in markdown
    assert "Related evidence elsewhere in package: ADM_Narrative.pdf: cost estimate." in markdown

def test_gsdt_module_folder_label_formats_known_plan_types():
    assert gsdt_module_folder_label("financial_responsibility") == "Financial Responsibility"
    assert gsdt_module_folder_label("pisc_site_closure") == "PISC and Site Closure Plan"
    assert gsdt_module_folder_label("testing_monitoring") == "Testing and Monitoring Plan"
    assert gsdt_module_folder_label("unknown") == "Unknown"