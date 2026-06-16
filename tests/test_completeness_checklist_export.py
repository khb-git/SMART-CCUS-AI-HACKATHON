from review.regulatory_citations import format_regulatory_citations
from review.report_export import (
    build_markdown_package_report,
    collect_reviewer_action_items,
    gsdt_module_folder_label,
    package_review_metrics,
)

from review.regulatory_citations import (
    format_item_regulatory_citations,
    format_regulatory_citations,
)

from review.report_export import collect_completeness_checklist_rows

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
    assert (
               "| Status | Required Item | GSDT Module/Folder | Regulatory Citation | "
               "File Name | Page Number | Notes |"
           ) in markdown
    assert (
               "| Evidence found | Coverage amount | Financial Responsibility | "
               "40 CFR 146.85 - Financial responsibility | ADM_Cost_Estimates.pdf | 4 |"
           ) in markdown
    assert (
               "| Missing | Financial instrument | Financial Responsibility | "
               "40 CFR 146.85 - Financial responsibility | ADM_Cost_Estimates.pdf | Not found |"
           ) in markdown
    assert "Related evidence elsewhere in package: ADM_Narrative.pdf: cost estimate." in markdown
    assert "## Package Review Metrics" in markdown
    assert "| Total checklist rows |" in markdown
    assert "| Page-located evidence percent |" in markdown
    assert "| Resolved percent |" in markdown
    assert "## Reviewer Action Items" in markdown
    assert "1." in markdown

def test_gsdt_module_folder_label_formats_known_plan_types():
    assert gsdt_module_folder_label("financial_responsibility") == "Financial Responsibility"
    assert gsdt_module_folder_label("pisc_site_closure") == "PISC and Site Closure Plan"
    assert gsdt_module_folder_label("testing_monitoring") == "Testing and Monitoring Plan"
    assert gsdt_module_folder_label("unknown") == "Unknown"

def test_package_review_metrics_count_status_confidence_and_page_locations():
    report = {
        "document_reviews": [
            {
                "document_name": "ADM_Cost_Estimates.pdf",
                "document_type": "financial_responsibility",
                "checklist_reports": {
                    "financial_responsibility": {
                        "findings": [
                            {
                                "item_id": "coverage_amount",
                                "label": "Coverage amount",
                                "status": "present",
                                "severity": "critical",
                                "requirement_level": "required",
                                "confidence": "High",
                                "finding": "Coverage amount appears addressed.",
                                "recommended_fix": "",
                                "evidence_locations": [
                                    {
                                        "file_name": "ADM_Cost_Estimates.pdf",
                                        "page_number": 4,
                                    }
                                ],
                            },
                            {
                                "item_id": "financial_instrument",
                                "label": "Financial instrument",
                                "status": "missing",
                                "severity": "critical",
                                "requirement_level": "required",
                                "confidence": "High",
                                "finding": "Financial instrument was not found.",
                                "recommended_fix": "Add the financial instrument.",
                                "evidence_locations": [],
                            },
                            {
                                "item_id": "inflation_adjustment",
                                "label": "Inflation adjustment",
                                "status": "evidence_found",
                                "severity": "moderate",
                                "requirement_level": "recommended",
                                "confidence": "Medium",
                                "finding": "Inflation adjustment evidence found.",
                                "recommended_fix": "",
                                "evidence_locations": [
                                    {
                                        "file_name": "ADM_Cost_Estimates.pdf",
                                        "page_number": 5,
                                    }
                                ],
                            },
                        ]
                    }
                },
            }
        ]
    }

    metrics = package_review_metrics(report)

    assert metrics["total_checklist_rows"] == 3
    assert metrics["present_rows"] == 1
    assert metrics["evidence_found_rows"] == 1
    assert metrics["missing_rows"] == 1
    assert metrics["unclear_rows"] == 0
    assert metrics["required_missing_rows"] == 1
    assert metrics["critical_missing_rows"] == 1
    assert metrics["high_confidence_rows"] == 2
    assert metrics["medium_confidence_rows"] == 1
    assert metrics["low_confidence_rows"] == 0
    assert metrics["page_located_rows"] == 2
    assert metrics["page_located_percent"] == "67%"
    assert metrics["resolved_rows"] == 2
    assert metrics["resolved_percent"] == "67%"

def test_collect_reviewer_action_items_prioritizes_missing_and_cross_document_rows():
    report = {
        "document_reviews": [
            {
                "document_name": "ADM_Cost_Estimates.pdf",
                "document_type": "financial_responsibility",
                "checklist_reports": {
                    "financial_responsibility": {
                        "findings": [
                            {
                                "item_id": "coverage_amount",
                                "label": "Coverage amount",
                                "status": "evidence_found",
                                "severity": "critical",
                                "requirement_level": "required",
                                "confidence": "Medium",
                                "finding": "Coverage amount evidence found.",
                                "recommended_fix": "Confirm amount covers all phases.",
                                "evidence_locations": [
                                    {
                                        "file_name": "ADM_Cost_Estimates.pdf",
                                        "page_number": 4,
                                    }
                                ],
                            },
                            {
                                "item_id": "financial_instrument",
                                "label": "Financial instrument",
                                "status": "missing",
                                "severity": "critical",
                                "requirement_level": "required",
                                "confidence": "High",
                                "finding": "Financial instrument was not found.",
                                "recommended_fix": "Add the financial instrument.",
                                "evidence_locations": [],
                                "related_package_evidence": [
                                    {
                                        "document_name": "ADM_Project_Narrative.pdf",
                                        "page_number": 7,
                                        "matched_terms": ["financial assurance"],
                                        "excerpt": "Financial assurance is referenced.",
                                    }
                                ],
                            },
                            {
                                "item_id": "inflation_adjustment",
                                "label": "Inflation adjustment",
                                "status": "unclear",
                                "severity": "moderate",
                                "requirement_level": "recommended",
                                "confidence": "Low",
                                "finding": "Inflation adjustment is unclear.",
                                "recommended_fix": "Clarify inflation adjustment.",
                                "evidence_locations": [],
                            },
                        ]
                    }
                },
            }
        ]
    }

    action_items = collect_reviewer_action_items(report)

    assert action_items
    assert any("critical missing" in item for item in action_items)
    assert any("required missing" in item for item in action_items)
    assert any("evidence-found" in item for item in action_items)
    assert any("low-confidence" in item for item in action_items)
    assert any("without page-located evidence" in item for item in action_items)
    assert any("cross-document related evidence" in item for item in action_items)

def test_format_regulatory_citations_maps_plan_types():
    assert (
        format_regulatory_citations("financial_responsibility")
        == "40 CFR 146.85 - Financial responsibility"
    )

    assert "40 CFR 146.90" in format_regulatory_citations("testing_monitoring")
    assert format_regulatory_citations("unknown") == "Not mapped"

def test_format_item_regulatory_citations_prefers_item_mapping_and_falls_back():
    assert (
        format_item_regulatory_citations(
            "testing_monitoring",
            "injection_pressure_monitoring",
        )
        == "40 CFR 146.90 - Testing and monitoring requirements"
    )

    assert (
        format_item_regulatory_citations(
            "testing_monitoring",
            "monitoring_frequency",
        )
        == (
            "40 CFR 146.90 - Testing and monitoring requirements; "
            "40 CFR 146.91 - Reporting requirements"
        )
    )

    assert (
        format_item_regulatory_citations(
            "financial_responsibility",
            "unknown_item",
        )
        == "40 CFR 146.85 - Financial responsibility"
    )

    assert (
        format_item_regulatory_citations(
            "unknown_plan_type",
            "unknown_item",
        )
        == "Not mapped"
    )

def test_collect_completeness_checklist_rows_uses_item_level_citation():
    report = {
        "document_reviews": [
            {
                "document_name": "Testing_Monitoring.pdf",
                "document_type": "testing_monitoring",
                "checklist_reports": {
                    "testing_monitoring": {
                        "findings": [
                            {
                                "item_id": "monitoring_frequency",
                                "label": "Monitoring frequency",
                                "status": "evidence_found",
                                "severity": "moderate",
                                "requirement_level": "required",
                                "confidence": "Medium",
                                "finding": "Monitoring frequency evidence found.",
                                "recommended_fix": "",
                                "evidence_locations": [
                                    {
                                        "file_name": "Testing_Monitoring.pdf",
                                        "page_number": 12,
                                    }
                                ],
                            }
                        ]
                    }
                },
            }
        ]
    }

    rows = collect_completeness_checklist_rows(report)

    assert rows[0]["regulatory_citation"] == (
        "40 CFR 146.90 - Testing and monitoring requirements; "
        "40 CFR 146.91 - Reporting requirements"
    )