from ui.app import (
    completeness_checklist_rows_for_display,
    maip_validation_rows_for_display,
)
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
    build_reviewer_confirmation_summary_section,
    append_maip_reviewer_confirmation_export,
    build_maip_reviewer_confirmation_export_section,
    is_maip_reviewer_row,
    split_maip_reviewer_rows,
    build_maip_deficiency_csv,
    filter_maip_deficiency_rows,
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

def test_build_reviewer_confirmation_summary_section_counts_rows():
    rows = [
        {
            "Reviewer Confirmation": "Pending review",
        },
        {
            "Reviewer Confirmation": "Confirmed",
        },
        {
            "Reviewer Confirmation": "Confirmed",
        },
        {
            "Reviewer Confirmation": "Needs follow-up",
        },
        {
            "Reviewer Confirmation": "Resolved after cross-reference",
        },
        {
            "Reviewer Confirmation": "Unexpected value",
        },
    ]

    markdown = build_reviewer_confirmation_summary_section(rows)

    assert "## Reviewer Confirmation Summary" in markdown
    assert "| Reviewer Confirmation | Count |" in markdown
    assert "| Pending review | 2 |" in markdown
    assert "| Confirmed | 2 |" in markdown
    assert "| Needs follow-up | 1 |" in markdown
    assert "| Not applicable | 0 |" in markdown
    assert "| Resolved after cross-reference | 1 |" in markdown

def test_reviewer_confirmation_summary_section_handles_empty_rows():
    markdown = build_reviewer_confirmation_summary_section([])

    assert "## Reviewer Confirmation Summary" in markdown
    assert "| Pending review | 0 |" in markdown
    assert "| Confirmed | 0 |" in markdown
    assert "| Needs follow-up | 0 |" in markdown
    assert "| Not applicable | 0 |" in markdown
    assert "| Resolved after cross-reference | 0 |" in markdown

def test_maip_validation_rows_for_display_formats_findings():
    package_report = {
        "maip_validation": {
            "overall_status": "missing_evidence",
            "summary": "MAIP validation complete.",
            "findings": [
                {
                    "finding_id": "maip_evidence_present",
                    "status": "missing_evidence",
                    "severity": "high",
                    "message": "The package does not provide a clear proposed MAIP.",
                    "recommended_action": "Reviewer should locate the proposed MAIP value.",
                    "supporting_values": [],
                },
                {
                    "finding_id": "maip_below_90_percent_fracture_pressure",
                    "status": "pass",
                    "severity": "info",
                    "message": "The proposed MAIP is below 90% of fracture pressure.",
                    "recommended_action": "Reviewer should confirm cited values.",
                    "supporting_values": [
                        {
                            "concept": "proposed_maip",
                            "value": 1800.0,
                            "unit": "psi",
                            "source_file": "Operating_Plan.pdf",
                            "page_number": 8,
                            "source_finding_id": "maximum_allowable_injection_pressure",
                            "source_label": "Maximum allowable injection pressure",
                            "matched_term": "maip",
                            "extraction_method": "concept_term_plus_pressure_value",
                            "confidence": "Medium",
                        }
                    ],
                },
            ],
        }
    }

    rows = maip_validation_rows_for_display(package_report)

    assert rows == [
        {
            "Review Key": "MAIP::maip_evidence_present",
            "Status": "ℹ️ Missing Evidence",
            "Severity": "High",
            "Finding": "maip_evidence_present",
            "Required Item": "maip_evidence_present",
            "GSDT Module/Folder": "MAIP Cross-Reference Validation",
            "Regulatory Citation": "Class VI MAIP cross-reference validation",
            "File Name": "See supporting values",
            "Page Number": "See supporting values",
            "Message": "The package does not provide a clear proposed MAIP.",
            "Recommended Action": "Reviewer should locate the proposed MAIP value.",
            "Supporting Values": "None",
            "Audit Trail": "None",
            "Notes": (
                "The package does not provide a clear proposed MAIP. "
                "Recommended action: Reviewer should locate the proposed MAIP value."
            ),
        },
        {
            "Review Key": "MAIP::maip_below_90_percent_fracture_pressure",
            "Status": "ℹ️ Pass",
            "Severity": "Info",
            "Finding": "maip_below_90_percent_fracture_pressure",
            "Required Item": "maip_below_90_percent_fracture_pressure",
            "GSDT Module/Folder": "MAIP Cross-Reference Validation",
            "Regulatory Citation": "Class VI MAIP cross-reference validation",
            "File Name": "See supporting values",
            "Page Number": "See supporting values",
            "Message": "The proposed MAIP is below 90% of fracture pressure.",
            "Recommended Action": "Reviewer should confirm cited values.",
            "Supporting Values": "proposed_maip: 1800.0 psi (Operating_Plan.pdf, page 8)",
            "Audit Trail": (
                "concept=proposed_maip; "
                "finding_id=maximum_allowable_injection_pressure; "
                "label=Maximum allowable injection pressure; "
                "matched_term=maip; "
                "method=concept_term_plus_pressure_value; "
                "confidence=Medium"
            ),
            "Notes": (
                "The proposed MAIP is below 90% of fracture pressure. "
                "Recommended action: Reviewer should confirm cited values."
            ),
        },
    ]


def test_maip_validation_rows_for_display_handles_missing_report():
    rows = maip_validation_rows_for_display({})

    assert rows == []

def test_maip_validation_rows_work_with_reviewer_confirmation_helpers():
    package_report = {
        "maip_validation": {
            "findings": [
                {
                    "finding_id": "maip_evidence_present",
                    "status": "missing_evidence",
                    "severity": "high",
                    "message": "The package does not provide a clear proposed MAIP.",
                    "recommended_action": "Reviewer should locate the proposed MAIP value.",
                    "supporting_values": [],
                }
            ],
        }
    }

    rows = maip_validation_rows_for_display(package_report)
    state = {
        reviewer_confirmation_state_key(rows[0]): "Needs follow-up",
        reviewer_note_state_key(rows[0]): "Applicant should provide the proposed MAIP source table.",
    }

    confirmed_rows = apply_reviewer_confirmations(rows, state)

    assert confirmed_rows[0]["Reviewer Confirmation"] == "Needs follow-up"
    assert (
        confirmed_rows[0]["Reviewer Notes"]
        == "Applicant should provide the proposed MAIP source table."
    )
    assert confirmed_rows[0]["Review Key"] == "MAIP::maip_evidence_present"

def test_is_maip_reviewer_row_identifies_maip_rows():
    assert is_maip_reviewer_row(
        {
            "Review Key": "MAIP::maip_evidence_present",
            "GSDT Module/Folder": "MAIP Cross-Reference Validation",
        }
    )

    assert not is_maip_reviewer_row(
        {
            "Review Key": "Financial Responsibility::Coverage amount::ADM.pdf",
            "GSDT Module/Folder": "Financial Responsibility",
        }
    )


def test_split_maip_reviewer_rows_separates_checklist_and_maip_rows():
    rows = [
        {
            "Review Key": "Financial Responsibility::Coverage amount::ADM.pdf",
            "GSDT Module/Folder": "Financial Responsibility",
        },
        {
            "Review Key": "MAIP::maip_evidence_present",
            "GSDT Module/Folder": "MAIP Cross-Reference Validation",
        },
    ]

    checklist_rows, maip_rows = split_maip_reviewer_rows(rows)

    assert len(checklist_rows) == 1
    assert len(maip_rows) == 1
    assert checklist_rows[0]["Review Key"].startswith("Financial Responsibility")
    assert maip_rows[0]["Review Key"] == "MAIP::maip_evidence_present"


def test_build_maip_reviewer_confirmation_export_section_includes_maip_rows():
    rows = [
        {
            "Review Key": "MAIP::maip_evidence_present",
            "Reviewer Confirmation": "Needs follow-up",
            "Reviewer Notes": "Applicant must provide MAIP source.",
            "Status": "ℹ️ Missing Evidence",
            "Severity": "High",
            "Finding": "maip_evidence_present",
            "Message": "The package does not provide a clear proposed MAIP.",
            "Recommended Action": "Reviewer should locate the proposed MAIP value.",
            "Supporting Values": "None",
            "GSDT Module/Folder": "MAIP Cross-Reference Validation",
        }
    ]

    markdown = build_maip_reviewer_confirmation_export_section(rows)

    assert "## MAIP Reviewer Confirmation Export" in markdown
    assert (
        "| Reviewer Confirmation | Reviewer Notes | Status | Severity | Finding | "
        "Message | Recommended Action | Supporting Values |"
    ) in markdown
    assert "Needs follow-up" in markdown
    assert "Applicant must provide MAIP source." in markdown
    assert "maip_evidence_present" in markdown


def test_build_maip_reviewer_confirmation_export_section_handles_no_maip_rows():
    rows = [
        {
            "Review Key": "Financial Responsibility::Coverage amount::ADM.pdf",
            "Reviewer Confirmation": "Confirmed",
            "GSDT Module/Folder": "Financial Responsibility",
        }
    ]

    markdown = build_maip_reviewer_confirmation_export_section(rows)

    assert "## MAIP Reviewer Confirmation Export" in markdown
    assert "No MAIP reviewer confirmation rows were available." in markdown


def test_append_maip_reviewer_confirmation_export_appends_section():
    base_markdown = "# Class VI Final Review Packet\n\nExisting report content.\n"
    rows = [
        {
            "Review Key": "MAIP::maip_evidence_present",
            "Reviewer Confirmation": "Needs follow-up",
            "Reviewer Notes": "Need MAIP source table.",
            "Status": "ℹ️ Missing Evidence",
            "Severity": "High",
            "Finding": "maip_evidence_present",
            "Message": "The package does not provide a clear proposed MAIP.",
            "Recommended Action": "Reviewer should locate the proposed MAIP value.",
            "Supporting Values": "None",
            "GSDT Module/Folder": "MAIP Cross-Reference Validation",
        }
    ]

    markdown = append_maip_reviewer_confirmation_export(base_markdown, rows)

    assert markdown.startswith("# Class VI Final Review Packet")
    assert "Existing report content." in markdown
    assert "## MAIP Reviewer Confirmation Export" in markdown
    assert "Need MAIP source table." in markdown

def test_filter_maip_deficiency_rows_returns_unresolved_maip_rows_only():
    rows = [
        {
            "Review Key": "MAIP::maip_evidence_present",
            "Status": "ℹ️ Missing Evidence",
            "Finding": "maip_evidence_present",
            "GSDT Module/Folder": "MAIP Cross-Reference Validation",
        },
        {
            "Review Key": "MAIP::maip_below_90_percent_fracture_pressure",
            "Status": "ℹ️ Pass",
            "Finding": "maip_below_90_percent_fracture_pressure",
            "GSDT Module/Folder": "MAIP Cross-Reference Validation",
        },
        {
            "Review Key": "MAIP::maip_below_aor_model_pressure",
            "Status": "ℹ️ Warning",
            "Finding": "maip_below_aor_model_pressure",
            "GSDT Module/Folder": "MAIP Cross-Reference Validation",
        },
        {
            "Review Key": "Financial Responsibility::Coverage amount::ADM.pdf",
            "Status": "🔴 Missing",
            "Required Item": "Coverage amount",
            "GSDT Module/Folder": "Financial Responsibility",
        },
    ]

    filtered_rows = filter_maip_deficiency_rows(rows)

    assert filtered_rows == [
        {
            "Review Key": "MAIP::maip_evidence_present",
            "Status": "ℹ️ Missing Evidence",
            "Finding": "maip_evidence_present",
            "GSDT Module/Folder": "MAIP Cross-Reference Validation",
        },
        {
            "Review Key": "MAIP::maip_below_aor_model_pressure",
            "Status": "ℹ️ Warning",
            "Finding": "maip_below_aor_model_pressure",
            "GSDT Module/Folder": "MAIP Cross-Reference Validation",
        },
    ]


def test_build_maip_deficiency_csv_includes_unresolved_maip_rows_only():
    rows = [
        {
            "Review Key": "MAIP::maip_evidence_present",
            "Reviewer Confirmation": "Needs follow-up",
            "Reviewer Notes": "Applicant must provide proposed MAIP.",
            "Status": "ℹ️ Missing Evidence",
            "Severity": "High",
            "Finding": "maip_evidence_present",
            "Message": "The package does not provide a clear proposed MAIP.",
            "Recommended Action": "Reviewer should locate the proposed MAIP value.",
            "Supporting Values": "None",
            "GSDT Module/Folder": "MAIP Cross-Reference Validation",
        },
        {
            "Review Key": "MAIP::maip_below_90_percent_fracture_pressure",
            "Reviewer Confirmation": "Confirmed",
            "Reviewer Notes": "Confirmed against operating plan.",
            "Status": "ℹ️ Pass",
            "Severity": "Info",
            "Finding": "maip_below_90_percent_fracture_pressure",
            "Message": "The proposed MAIP is below 90% of fracture pressure.",
            "Recommended Action": "Reviewer should confirm cited values.",
            "Supporting Values": "proposed_maip: 1800.0 psi",
            "GSDT Module/Folder": "MAIP Cross-Reference Validation",
        },
        {
            "Review Key": "Financial Responsibility::Coverage amount::ADM.pdf",
            "Reviewer Confirmation": "Needs follow-up",
            "Reviewer Notes": "Need amount.",
            "Status": "🔴 Missing",
            "Required Item": "Coverage amount",
            "GSDT Module/Folder": "Financial Responsibility",
        },
    ]

    csv_text = build_maip_deficiency_csv(rows)

    assert (
        "Reviewer Confirmation,Reviewer Notes,Status,Severity,Finding,Message,"
        "Recommended Action,Supporting Values"
    ) in csv_text
    assert "maip_evidence_present" in csv_text
    assert "Applicant must provide proposed MAIP." in csv_text
    assert "maip_below_90_percent_fracture_pressure" not in csv_text
    assert "Coverage amount" not in csv_text