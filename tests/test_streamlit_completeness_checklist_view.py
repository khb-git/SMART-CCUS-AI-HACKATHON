from ui.app import completeness_checklist_rows_for_display
from ui.reviewer_workflow import (
    append_reviewer_confirmation_export,
    apply_reviewer_confirmations,
    build_completeness_checklist_csv,
    build_deficiency_checklist_csv,
    build_reviewer_confirmation_export_section,
    filter_deficiency_rows,
    filter_rows_by_reviewer_confirmation,
    reviewer_confirmation_counts,
    reviewer_confirmation_state_key,
    reviewer_note_state_key,
    build_reviewer_state_export,
    parse_reviewer_state_import,
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
            "Regulatory Citation": "40 CFR 146.85 - Financial responsibility",
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
            "Regulatory Citation": "40 CFR 146.85 - Financial responsibility",
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
            "Regulatory Citation": "40 CFR 146.85 - Financial responsibility",
            "File Name": "ADM_Cost_Estimates.pdf",
            "Page Number": "Not found",
            "Notes": "Financial instrument missing.",
        },
    ]

    csv_text = build_completeness_checklist_csv(rows)

    assert (
        "Reviewer Confirmation,Reviewer Notes,Status,Required Item,GSDT Module/Folder,"
        "Regulatory Citation,File Name,Page Number,Notes"
    ) in csv_text
    assert (
        "Confirmed,Confirmed against cost estimate table.,✅ Present,Coverage amount,"
        "Financial Responsibility,40 CFR 146.85 - Financial responsibility,"
        "ADM_Cost_Estimates.pdf,4,Coverage amount evidence found."
    ) in csv_text
    assert (
        "Needs follow-up,Need the actual financial instrument document.,🔴 Missing,"
        "Financial instrument,Financial Responsibility,"
        "40 CFR 146.85 - Financial responsibility,ADM_Cost_Estimates.pdf,"
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

def test_apply_reviewer_confirmations_uses_supplied_state():
    row = {
        "Review Key": "Financial Responsibility::Coverage amount::ADM_Cost_Estimates.pdf",
        "Required Item": "Coverage amount",
    }

    confirmation_key = reviewer_confirmation_state_key(row)
    note_key = reviewer_note_state_key(row)

    rows = apply_reviewer_confirmations(
        [row],
        {
            confirmation_key: "Confirmed",
            note_key: "Confirmed against cost estimate table.",
        },
    )

    assert rows == [
        {
            "Review Key": "Financial Responsibility::Coverage amount::ADM_Cost_Estimates.pdf",
            "Required Item": "Coverage amount",
            "Reviewer Confirmation": "Confirmed",
            "Reviewer Notes": "Confirmed against cost estimate table.",
        }
    ]

def test_filter_deficiency_rows_returns_only_unresolved_rows():
    rows = [
        {
            "Status": "✅ Present",
            "Required Item": "Coverage amount",
        },
        {
            "Status": "🟡 Evidence found",
            "Required Item": "Monitoring frequency",
        },
        {
            "Status": "🔴 Missing",
            "Required Item": "Financial instrument",
        },
        {
            "Status": "🟠 Unclear",
            "Required Item": "Corrective action narrative",
        },
    ]

    filtered_rows = filter_deficiency_rows(rows)

    assert filtered_rows == [
        {
            "Status": "🟡 Evidence found",
            "Required Item": "Monitoring frequency",
        },
        {
            "Status": "🔴 Missing",
            "Required Item": "Financial instrument",
        },
        {
            "Status": "🟠 Unclear",
            "Required Item": "Corrective action narrative",
        },
    ]


def test_build_deficiency_checklist_csv_excludes_present_rows():
    rows = [
        {
            "Reviewer Confirmation": "Confirmed",
            "Reviewer Notes": "Looks complete.",
            "Status": "✅ Present",
            "Required Item": "Coverage amount",
            "GSDT Module/Folder": "Financial Responsibility",
            "Regulatory Citation": "40 CFR 146.85 - Financial responsibility",
            "File Name": "ADM_Cost_Estimates.pdf",
            "Page Number": "4",
            "Notes": "Coverage amount evidence found.",
        },
        {
            "Reviewer Confirmation": "Needs follow-up",
            "Reviewer Notes": "Need actual instrument.",
            "Status": "🔴 Missing",
            "Required Item": "Financial instrument",
            "GSDT Module/Folder": "Financial Responsibility",
            "Regulatory Citation": "40 CFR 146.85 - Financial responsibility",
            "File Name": "ADM_Cost_Estimates.pdf",
            "Page Number": "Not found",
            "Notes": "Financial instrument missing.",
        },
        {
            "Reviewer Confirmation": "Pending review",
            "Reviewer Notes": "Confirm monitoring interval.",
            "Status": "🟡 Evidence found",
            "Required Item": "Monitoring frequency",
            "GSDT Module/Folder": "Testing and Monitoring Plan",
            "Regulatory Citation": (
                "40 CFR 146.90 - Testing and monitoring requirements; "
                "40 CFR 146.91 - Reporting requirements"
            ),
            "File Name": "Testing_Monitoring.pdf",
            "Page Number": "12",
            "Notes": "Monitoring frequency evidence found.",
        },
    ]

    csv_text = build_deficiency_checklist_csv(rows)

    assert "Financial instrument" in csv_text
    assert "Monitoring frequency" in csv_text
    assert "Need actual instrument." in csv_text
    assert "Confirm monitoring interval." in csv_text
    assert "Coverage amount" not in csv_text
    assert "Looks complete." not in csv_text

def test_build_reviewer_state_export_includes_confirmations_and_notes():
    rows = [
        {
            "Review Key": "Financial Responsibility::Financial instrument::ADM_Cost_Estimates.pdf",
            "Reviewer Confirmation": "Needs follow-up",
            "Reviewer Notes": "Need actual instrument.",
            "Status": "🔴 Missing",
            "Required Item": "Financial instrument",
            "GSDT Module/Folder": "Financial Responsibility",
            "Regulatory Citation": "40 CFR 146.85 - Financial responsibility",
            "File Name": "ADM_Cost_Estimates.pdf",
            "Page Number": "Not found",
        }
    ]

    json_text = build_reviewer_state_export(
        rows,
        package_name="uploaded_package",
    )

    assert '"version": 1' in json_text
    assert '"package_name": "uploaded_package"' in json_text
    assert "Financial instrument" in json_text
    assert "Needs follow-up" in json_text
    assert "Need actual instrument." in json_text


def test_parse_reviewer_state_import_returns_session_state_updates():
    json_text = """
    {
      "version": 1,
      "package_name": "uploaded_package",
      "reviewer_state": [
        {
          "Review Key": "Financial Responsibility::Financial instrument::ADM_Cost_Estimates.pdf",
          "Reviewer Confirmation": "Needs follow-up",
          "Reviewer Notes": "Need actual instrument."
        }
      ]
    }
    """

    updates = parse_reviewer_state_import(json_text)

    assert updates[
        "reviewer_confirmation_Financial_Responsibility__Financial_instrument__ADM_Cost_Estimates_pdf"
    ] == "Needs follow-up"
    assert updates[
        "reviewer_note_Financial_Responsibility__Financial_instrument__ADM_Cost_Estimates_pdf"
    ] == "Need actual instrument."


def test_parse_reviewer_state_import_defaults_invalid_confirmation_to_pending():
    json_text = """
    {
      "version": 1,
      "reviewer_state": [
        {
          "Review Key": "Testing::Monitoring frequency::Testing_Monitoring.pdf",
          "Reviewer Confirmation": "Invalid status",
          "Reviewer Notes": "Check this."
        }
      ]
    }
    """

    updates = parse_reviewer_state_import(json_text)

    assert updates[
        "reviewer_confirmation_Testing__Monitoring_frequency__Testing_Monitoring_pdf"
    ] == "Pending review"
    assert updates[
        "reviewer_note_Testing__Monitoring_frequency__Testing_Monitoring_pdf"
    ] == "Check this."


def test_parse_reviewer_state_import_rejects_invalid_json():
    try:
        parse_reviewer_state_import("not valid json")
    except ValueError as exc:
        assert "not valid JSON" in str(exc)
    else:
        raise AssertionError("Expected invalid reviewer state JSON to raise ValueError")