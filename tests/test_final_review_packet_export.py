from review.report_export import (
    build_deficiency_table_section,
    build_final_review_packet,
    collect_deficiency_rows,
)


def sample_package_response():
    return {
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
                                    "confidence": "Medium",
                                    "finding": "Coverage amount evidence found.",
                                    "recommended_fix": "Confirm amount covers all phases.",
                                    "matched_evidence_group_names": ["cost_basis"],
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
                                    "matched_evidence_group_names": [],
                                    "evidence_locations": [],
                                },
                                {
                                    "item_id": "inflation_adjustment",
                                    "label": "Inflation adjustment",
                                    "status": "present",
                                    "severity": "moderate",
                                    "requirement_level": "recommended",
                                    "confidence": "High",
                                    "finding": "Inflation adjustment appears addressed.",
                                    "recommended_fix": "",
                                    "matched_evidence_group_names": [],
                                    "evidence_locations": [
                                        {
                                            "file_name": "ADM_Cost_Estimates.pdf",
                                            "page_number": 5,
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


def test_collect_deficiency_rows_excludes_present_rows():
    report = sample_package_response()["report"]

    rows = collect_deficiency_rows(report)

    assert [row["required_item"] for row in rows] == [
        "Financial instrument",
        "Coverage amount",
    ]


def test_build_deficiency_table_section_includes_regulatory_citations():
    report = sample_package_response()["report"]

    markdown = "\n".join(build_deficiency_table_section(report))

    assert "## Deficiency Table" in markdown
    assert (
        "| Status | Required Item | GSDT Module/Folder | Regulatory Citation | "
        "File Name | Page Number | Reviewer Follow-Up |"
    ) in markdown
    assert "Financial instrument" in markdown
    assert "Coverage amount" in markdown
    assert "40 CFR 146.85 - Financial responsibility" in markdown
    assert "Inflation adjustment" not in markdown


def test_build_final_review_packet_includes_core_sections():
    markdown = build_final_review_packet(sample_package_response())

    assert "# Class VI Final Review Packet" in markdown
    assert "## Packet Purpose" in markdown
    assert "## Final Package Summary" in markdown
    assert "## Package Review Metrics" in markdown
    assert "## Reviewer Action Items" in markdown
    assert "## Deficiency Table" in markdown
    assert "## Completeness Checklist Review" in markdown
    assert "## Reviewer Sign-Off" in markdown
    assert "## Appendix: Full Package Review Report" in markdown
    assert "Financial instrument" in markdown
    assert "40 CFR 146.85 - Financial responsibility" in markdown