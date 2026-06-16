from ui.app import (
    append_reviewer_confirmation_export,
    build_completeness_checklist_csv,
    build_reviewer_confirmation_export_section,
    completeness_checklist_rows_for_display,
    filter_rows_by_reviewer_confirmation,
    reviewer_confirmation_counts,
    reviewer_confirmation_state_key,
    reviewer_note_state_key,
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

def test_build_reviewer_confirmation_export_section_includes_selected_states():
    rows = [
        {
            "Reviewer Confirmation": "Confirmed",
            "Reviewer Notes": "Confirmed against cost estimate table.",
            "Status": "✅ Present",
            "Required Item": "Coverage amount",
            "GSDT Module/Folder": "Financial Responsibility",
            "File Name": "ADM_Cost_Estimates.pdf",
            "Page Number": "4",
        },
        {
            "Reviewer Confirmation": "Needs follow-up",
            "Reviewer Notes": "Need the actual financial instrument document.",
            "Status": "🔴 Missing",
            "Required Item": "Financial instrument",
            "GSDT Module/Folder": "Financial Responsibility",
            "File Name": "ADM_Cost_Estimates.pdf",
            "Page Number": "Not found",
        },
    ]

    markdown = build_reviewer_confirmation_export_section(rows)

    assert "## Reviewer Confirmation Export" in markdown
    assert (
        "| Reviewer Confirmation | Reviewer Notes | Status | Required Item | "
        "GSDT Module/Folder | File Name | Page Number |"
    ) in markdown
    assert (
        "| Confirmed | Confirmed against cost estimate table. | ✅ Present | "
        "Coverage amount | Financial Responsibility | ADM_Cost_Estimates.pdf | 4 |"
    ) in markdown
    assert (
        "| Needs follow-up | Need the actual financial instrument document. | 🔴 Missing | "
        "Financial instrument | Financial Responsibility | ADM_Cost_Estimates.pdf | Not found |"
    ) in markdown


def test_append_reviewer_confirmation_export_appends_section():
    base_markdown = "# Class VI Package Review Report\n\nExisting report content.\n"
    rows = [
        {
            "Reviewer Confirmation": "Resolved after cross-reference",
            "Status": "🟡 Evidence found",
            "Required Item": "Inflation adjustment",
            "GSDT Module/Folder": "Financial Responsibility",
            "File Name": "ADM_Cost_Estimates.pdf",
            "Page Number": "5",
        }
    ]

    markdown = append_reviewer_confirmation_export(base_markdown, rows)

    assert markdown.startswith("# Class VI Package Review Report")
    assert "Existing report content." in markdown
    assert "## Reviewer Confirmation Export" in markdown
    assert "Resolved after cross-reference" in markdown

def test_build_completeness_checklist_csv_includes_reviewer_confirmations():
    rows = [
        {
            "Reviewer Confirmation": "Confirmed",
            "Reviewer Notes": "Confirmed against cost estimate table.",
            "Status": "✅ Present",
            "Required Item": "Coverage amount",
            "GSDT Module/Folder": "Financial Responsibility",
            "File Name": "ADM_Cost_Estimates.pdf",
            "Page Number": "4",
            "Notes": "Coverage amount evidence found.",
        },
        {
            "Reviewer Confirmation": "Needs follow-up",
            "Reviewer Notes": "Need the actual financial instrument document.",
            "Status": "🔴 Missing",
            "Required Item": "Financial instrument",
            "GSDT Module/Folder": "Financial Responsibility",
            "File Name": "ADM_Cost_Estimates.pdf",
            "Page Number": "Not found",
            "Notes": "Financial instrument missing.",
        },
    ]

    csv_text = build_completeness_checklist_csv(rows)

    assert (
        "Reviewer Confirmation,Reviewer Notes,Status,Required Item,GSDT Module/Folder,"
        "File Name,Page Number,Notes"
    ) in csv_text
    assert (
        "Confirmed,Confirmed against cost estimate table.,✅ Present,Coverage amount,"
        "Financial Responsibility,ADM_Cost_Estimates.pdf,4,Coverage amount evidence found."
    ) in csv_text
    assert (
        "Needs follow-up,Need the actual financial instrument document.,🔴 Missing,"
        "Financial instrument,Financial Responsibility,ADM_Cost_Estimates.pdf,"
        "Not found,Financial instrument missing."
    ) in csv_text

def test_filter_rows_by_reviewer_confirmation_returns_matching_rows():
    rows = [
        {
            "Reviewer Confirmation": "Pending review",
            "Required Item": "Coverage amount",
        },
        {
            "Reviewer Confirmation": "Confirmed",
            "Required Item": "Financial instrument",
        },
        {
            "Reviewer Confirmation": "Needs follow-up",
            "Required Item": "Inflation adjustment",
        },
        {
            "Reviewer Confirmation": "Resolved after cross-reference",
            "Required Item": "Cross-reference row",
        },
    ]

    filtered_rows = filter_rows_by_reviewer_confirmation(
        rows,
        ["Confirmed", "Needs follow-up"],
    )

    assert filtered_rows == [
        {
            "Reviewer Confirmation": "Confirmed",
            "Required Item": "Financial instrument",
        },
        {
            "Reviewer Confirmation": "Needs follow-up",
            "Required Item": "Inflation adjustment",
        },
    ]


def test_filter_rows_by_reviewer_confirmation_returns_all_rows_when_empty():
    rows = [
        {
            "Reviewer Confirmation": "Pending review",
            "Required Item": "Coverage amount",
        },
        {
            "Reviewer Confirmation": "Confirmed",
            "Required Item": "Financial instrument",
        },
    ]

    assert filter_rows_by_reviewer_confirmation(rows, []) == rows

def test_reviewer_note_state_key_is_stable_and_safe():
    row = {
        "Review Key": "Financial Responsibility::Coverage amount::ADM_Cost_Estimates.pdf",
    }

    key = reviewer_note_state_key(row)

    assert key == (
        "reviewer_note_"
        "Financial_Responsibility__Coverage_amount__ADM_Cost_Estimates_pdf"
    )