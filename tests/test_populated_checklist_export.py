from review.checklist_population import (
    ChecklistPopulationStatus,
    PopulatedChecklistEvidence,
    PopulatedChecklistRow,
    ReviewerConfirmationStatus,
    build_markdown_populated_checklist,
    build_populated_checklist,
)


def test_build_markdown_populated_checklist_includes_summary_and_sections():
    rows = [
        PopulatedChecklistRow(
            section_title="GENERAL INFORMATION",
            checklist_item=(
                "A listing of activities requiring RCRA, UIC, NPDES, or PSD permits."
            ),
            citation="40 CFR 144.31(e)(1)",
            status=ChecklistPopulationStatus.PRESENT,
            gsdt_module_folder="project narrative",
            file_name="Project_Narrative.pdf",
            page_number=12,
            evidence_excerpt=(
                "The applicant lists activities requiring UIC and NPDES permits."
            ),
            system_notes="Populated from existing package review evidence.",
            reviewer_notes="Reviewer confirmed.",
            reviewer_confirmation=ReviewerConfirmationStatus.CONFIRMED,
            confidence="High",
            evidence=[
                PopulatedChecklistEvidence(
                    file_name="Project_Narrative.pdf",
                    page_number=12,
                    excerpt=(
                        "The applicant lists activities requiring UIC and NPDES permits."
                    ),
                    source_label="Environmental permits",
                    confidence="High",
                )
            ],
        ),
        PopulatedChecklistRow(
            section_title="PLANNED WELL OPERATIONS",
            checklist_item="Proposed average and maximum injection pressure.",
            citation="40 CFR 146.82(a)(7)(ii)",
            status=ChecklistPopulationStatus.REDACTED,
            gsdt_module_folder="site operating",
            file_name="Operating_Plan.pdf",
            page_number=8,
            evidence_excerpt="Maximum injection pressure: [REDACTED] psi.",
            system_notes=(
                "Relevant evidence appears present, but the value is redacted."
            ),
            confidence="High",
        ),
    ]

    checklist = build_populated_checklist(
        package_name="uploaded_package",
        rows=rows,
    )

    markdown = build_markdown_populated_checklist(checklist)

    assert "# Populated Class VI Completeness Checklist" in markdown
    assert "Package name: `uploaded_package`" in markdown
    assert "## Section Summary" in markdown
    assert "GENERAL INFORMATION" in markdown
    assert "PLANNED WELL OPERATIONS" in markdown
    assert "Present rows: 1" in markdown
    assert "Redacted rows: 1" in markdown
    assert "Project_Narrative.pdf" in markdown
    assert "Operating_Plan.pdf" in markdown
    assert "40 CFR 144.31(e)(1)" in markdown
    assert "40 CFR 146.82(a)(7)(ii)" in markdown
    assert "Maximum injection pressure: [REDACTED] psi." in markdown
    assert "Reviewer confirmed." in markdown


def test_build_markdown_populated_checklist_handles_missing_rows():
    rows = [
        PopulatedChecklistRow(
            section_title="GENERAL INFORMATION",
            checklist_item="Name, mailing address, and location of the facility.",
            citation="40 CFR 144.31(e)(2)",
            status=ChecklistPopulationStatus.MISSING,
            system_notes=(
                "No matching package review evidence was found for this checklist row."
            ),
        )
    ]

    checklist = build_populated_checklist(
        package_name="missing_package",
        rows=rows,
    )

    markdown = build_markdown_populated_checklist(checklist)

    assert "Package name: `missing_package`" in markdown
    assert "Missing rows: 1" in markdown
    assert "Status: **Missing**" in markdown
    assert "_No evidence excerpt populated._" in markdown
    assert "No matching package review evidence" in markdown
    assert "_No reviewer notes._" in markdown


def test_build_markdown_populated_checklist_escapes_table_pipes():
    rows = [
        PopulatedChecklistRow(
            section_title="GENERAL | INFORMATION",
            checklist_item="Facility name and address.",
            status=ChecklistPopulationStatus.PRESENT,
            file_name="Project|Narrative.pdf",
            evidence=[
                PopulatedChecklistEvidence(
                    file_name="Project|Narrative.pdf",
                    page_number=3,
                    excerpt="Facility | address evidence.",
                    confidence="Medium",
                )
            ],
        )
    ]

    checklist = build_populated_checklist(
        package_name="pipe_package",
        rows=rows,
    )

    markdown = build_markdown_populated_checklist(checklist)

    assert "GENERAL \\| INFORMATION" in markdown
    assert "Project\\|Narrative.pdf" in markdown
    assert "Facility \\| address evidence." in markdown

def test_build_markdown_populated_checklist_labels_missing_row_evidence_as_related():
    rows = [
        PopulatedChecklistRow(
            section_title="AoR and Corrective Action Plan Checklist",
            checklist_item="Artificial penetration evaluation",
            citation="40 CFR 146.84",
            status=ChecklistPopulationStatus.MISSING,
            gsdt_module_folder="aor corrective action",
            file_name="Marquis_AoR_and_Corrective_Action_Plan.pdf",
            page_number=5,
            evidence_excerpt=(
                "Figure 2-34: Map showing the modeled CO2 plume footprint, "
                "AoR, and existing and proposed project wells within the AoR."
            ),
            system_notes="Populated from existing package review evidence.",
            confidence="Medium",
            evidence=[
                PopulatedChecklistEvidence(
                    file_name="Marquis_AoR_and_Corrective_Action_Plan.pdf",
                    page_number=5,
                    excerpt=(
                        "Figure 2-34: Map showing the modeled CO2 plume footprint, "
                        "AoR, and existing and proposed project wells within the AoR."
                    ),
                    confidence="Medium",
                )
            ],
        )
    ]

    checklist = build_populated_checklist(
        package_name="uploaded_package",
        rows=rows,
    )

    markdown = build_markdown_populated_checklist(checklist)

    assert "Status: **Missing**" in markdown
    assert "**Related evidence excerpt**" in markdown
    assert "**Related evidence note**" in markdown
    assert "did not determine that it fully satisfies this checklist row" in markdown
    assert "**Related evidence locations**" in markdown
    assert "**Evidence excerpt**" not in markdown