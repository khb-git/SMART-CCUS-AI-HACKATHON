from review.checklist_population import (
    ChecklistPopulationStatus,
    ChecklistSectionStatus,
    PopulatedChecklistEvidence,
    PopulatedChecklistRow,
    ReviewerConfirmationStatus,
    build_populated_checklist,
    build_section_summary,
    determine_section_status,
)


def test_populated_checklist_row_serializes_to_dict():
    evidence = PopulatedChecklistEvidence(
        file_name="Project_Narrative.pdf",
        page_number=12,
        excerpt="The applicant lists permits required under UIC and NPDES.",
        source_label="General information",
        confidence="High",
    )

    row = PopulatedChecklistRow(
        section_title="GENERAL INFORMATION",
        checklist_item=(
            "A listing of the activities conducted by the applicant which "
            "require RCRA, UIC, NPDES, or PSD permits."
        ),
        citation="40 CFR 144.31(e)(1)",
        status=ChecklistPopulationStatus.PRESENT,
        gsdt_module_folder="General Information",
        file_name="Project_Narrative.pdf",
        page_number=12,
        evidence_excerpt=(
            "The applicant lists permits required under UIC and NPDES."
        ),
        system_notes="Candidate evidence found in project narrative.",
        reviewer_notes="Reviewer confirmed this satisfies the row.",
        reviewer_confirmation=ReviewerConfirmationStatus.CONFIRMED,
        confidence="High",
        evidence=[evidence],
    )

    row_dict = row.to_dict()

    assert row_dict["section_title"] == "GENERAL INFORMATION"
    assert row_dict["status"] == "present"
    assert row_dict["citation"] == "40 CFR 144.31(e)(1)"
    assert row_dict["gsdt_module_folder"] == "General Information"
    assert row_dict["file_name"] == "Project_Narrative.pdf"
    assert row_dict["page_number"] == 12
    assert row_dict["reviewer_confirmation"] == "confirmed"
    assert row_dict["evidence"][0]["confidence"] == "High"


def test_determine_section_status_green_when_required_rows_present():
    rows = [
        PopulatedChecklistRow(
            section_title="GENERAL INFORMATION",
            checklist_item="Facility name and address.",
            status=ChecklistPopulationStatus.PRESENT,
        ),
        PopulatedChecklistRow(
            section_title="GENERAL INFORMATION",
            checklist_item="Operator information.",
            status=ChecklistPopulationStatus.PRESENT,
        ),
    ]

    assert determine_section_status(rows) == ChecklistSectionStatus.GREEN


def test_determine_section_status_red_when_required_row_missing():
    rows = [
        PopulatedChecklistRow(
            section_title="GENERAL INFORMATION",
            checklist_item="Facility name and address.",
            status=ChecklistPopulationStatus.PRESENT,
        ),
        PopulatedChecklistRow(
            section_title="GENERAL INFORMATION",
            checklist_item="Permit activities listing.",
            status=ChecklistPopulationStatus.MISSING,
        ),
    ]

    assert determine_section_status(rows) == ChecklistSectionStatus.RED


def test_determine_section_status_yellow_for_unclear_redacted_or_attention():
    unclear_rows = [
        PopulatedChecklistRow(
            section_title="PLANNED WELL OPERATIONS",
            checklist_item="Maximum injection pressure.",
            status=ChecklistPopulationStatus.UNCLEAR,
        )
    ]

    redacted_rows = [
        PopulatedChecklistRow(
            section_title="PLANNED WELL OPERATIONS",
            checklist_item="Maximum injection pressure.",
            status=ChecklistPopulationStatus.REDACTED,
        )
    ]

    attention_rows = [
        PopulatedChecklistRow(
            section_title="PLANNED WELL OPERATIONS",
            checklist_item="Maximum injection pressure.",
            status=ChecklistPopulationStatus.NEEDS_REVIEWER_ATTENTION,
        )
    ]

    assert determine_section_status(unclear_rows) == ChecklistSectionStatus.YELLOW
    assert determine_section_status(redacted_rows) == ChecklistSectionStatus.YELLOW
    assert determine_section_status(attention_rows) == ChecklistSectionStatus.YELLOW


def test_determine_section_status_gray_for_only_optional_not_applicable_rows():
    rows = [
        PopulatedChecklistRow(
            section_title="INJECTION DEPTH WAIVER REQUEST",
            checklist_item="Injection depth waiver request.",
            status=ChecklistPopulationStatus.NOT_APPLICABLE_OPTIONAL,
            is_optional=True,
        )
    ]

    assert determine_section_status(rows) == ChecklistSectionStatus.GRAY


def test_build_section_summary_counts_row_statuses():
    rows = [
        PopulatedChecklistRow(
            section_title="GENERAL INFORMATION",
            checklist_item="Facility name and address.",
            status=ChecklistPopulationStatus.PRESENT,
        ),
        PopulatedChecklistRow(
            section_title="GENERAL INFORMATION",
            checklist_item="Permit activities listing.",
            status=ChecklistPopulationStatus.MISSING,
        ),
        PopulatedChecklistRow(
            section_title="GENERAL INFORMATION",
            checklist_item="Indian lands statement.",
            status=ChecklistPopulationStatus.UNCLEAR,
        ),
        PopulatedChecklistRow(
            section_title="GENERAL INFORMATION",
            checklist_item="Optional item.",
            status=ChecklistPopulationStatus.NOT_APPLICABLE_OPTIONAL,
            is_optional=True,
        ),
    ]

    summary = build_section_summary(
        section_title="GENERAL INFORMATION",
        rows=rows,
    )

    summary_dict = summary.to_dict()

    assert summary.status == ChecklistSectionStatus.RED
    assert summary_dict["total_rows"] == 4
    assert summary_dict["present_rows"] == 1
    assert summary_dict["missing_rows"] == 1
    assert summary_dict["unclear_rows"] == 1
    assert summary_dict["optional_not_applicable_rows"] == 1


def test_build_populated_checklist_preserves_section_order():
    rows = [
        PopulatedChecklistRow(
            section_title="GENERAL INFORMATION",
            checklist_item="Facility name and address.",
            status=ChecklistPopulationStatus.PRESENT,
        ),
        PopulatedChecklistRow(
            section_title="TESTING AND MONITORING PLAN",
            checklist_item="Continuous recording of operational parameters.",
            status=ChecklistPopulationStatus.REDACTED,
        ),
        PopulatedChecklistRow(
            section_title="GENERAL INFORMATION",
            checklist_item="Permit activities listing.",
            status=ChecklistPopulationStatus.PRESENT,
        ),
    ]

    checklist = build_populated_checklist(
        package_name="uploaded_package",
        rows=rows,
    )

    checklist_dict = checklist.to_dict()

    assert checklist_dict["package_name"] == "uploaded_package"
    assert len(checklist_dict["rows"]) == 3
    assert len(checklist_dict["section_summaries"]) == 2
    assert checklist_dict["section_summaries"][0]["section_title"] == (
        "GENERAL INFORMATION"
    )
    assert checklist_dict["section_summaries"][0]["status"] == "green"
    assert checklist_dict["section_summaries"][1]["section_title"] == (
        "TESTING AND MONITORING PLAN"
    )
    assert checklist_dict["section_summaries"][1]["status"] == "yellow"