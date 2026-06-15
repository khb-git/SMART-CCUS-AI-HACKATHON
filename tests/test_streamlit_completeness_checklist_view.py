from ui.app import completeness_checklist_rows_for_display


def test_completeness_checklist_rows_for_display_formats_rows():
    package_report = {
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
                                "finding": "Coverage amount: evidence found.",
                                "recommended_fix": "Add comparison to estimated costs.",
                                "evidence_locations": [
                                    {
                                        "file_name": "ADM_Cost_Estimates.pdf",
                                        "page_number": 4,
                                    }
                                ],
                            }
                        ]
                    }
                },
            }
        ]
    }

    rows = completeness_checklist_rows_for_display(package_report)

    assert rows == [
        {
            "Status": "🟡 Evidence found",
            "Required Item": "Coverage amount",
            "GSDT Module/Folder": "Financial Responsibility",
            "File Name": "ADM_Cost_Estimates.pdf",
            "Page Number": "4",
            "Notes": (
                "Coverage amount: evidence found. "
                "Recommended fix: Add comparison to estimated costs."
            ),
        }
    ]