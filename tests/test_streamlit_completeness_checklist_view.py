from ui.app import (
    completeness_checklist_rows_for_display,
    reviewer_confirmation_counts,
    reviewer_confirmation_state_key,
)


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
            "Review Key": "Financial Responsibility::Coverage amount::ADM_Cost_Estimates.pdf",
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

def test_reviewer_confirmation_state_key_is_stable_and_safe():
    row = {
        "Review Key": "Financial Responsibility::Coverage amount::ADM_Cost_Estimates.pdf",
    }

    key = reviewer_confirmation_state_key(row)

    assert key == (
        "reviewer_confirmation_"
        "Financial_Responsibility__Coverage_amount__ADM_Cost_Estimates_pdf"
    )

def test_reviewer_confirmation_counts_summarizes_rows():
    rows = [
        {"Reviewer Confirmation": "Pending review"},
        {"Reviewer Confirmation": "Confirmed"},
        {"Reviewer Confirmation": "Confirmed"},
        {"Reviewer Confirmation": "Needs follow-up"},
        {"Reviewer Confirmation": "Not applicable"},
        {"Reviewer Confirmation": "Resolved after cross-reference"},
        {"Reviewer Confirmation": "Unexpected value"},
    ]

    counts = reviewer_confirmation_counts(rows)

    assert counts["Pending review"] == 2
    assert counts["Confirmed"] == 2
    assert counts["Needs follow-up"] == 1
    assert counts["Not applicable"] == 1
    assert counts["Resolved after cross-reference"] == 1