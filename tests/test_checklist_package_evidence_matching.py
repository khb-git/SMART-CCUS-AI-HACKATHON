from review.checklist_population import (
    ChecklistPopulationStatus,
    ChecklistSectionStatus,
    build_checklist_row_retrieval_query,
    build_populated_checklist_from_package_report,
    collect_package_review_findings_for_population,
    infer_checklist_population_status_from_finding,
    populate_checklist_row_from_query,
    score_query_against_package_finding,
)
from review.types import (
    ReviewChecklist,
    ReviewChecklistItem,
    ReviewRequirementLevel,
    ReviewSeverity,
)


def make_general_information_checklist() -> ReviewChecklist:
    item = ReviewChecklistItem(
        item_id="permit_activities_listing",
        label=(
            "A listing of the activities conducted by the applicant which "
            "require RCRA, UIC, NPDES, or PSD permits. "
            "[40 CFR 144.31(e)(1)]"
        ),
        description=(
            "Identify applicant activities requiring environmental permits."
        ),
        requirement_level=ReviewRequirementLevel.REQUIRED,
        severity=ReviewSeverity.CRITICAL,
        expected_evidence_terms=[
            "RCRA",
            "UIC",
            "NPDES",
            "PSD",
            "environmental permits",
        ],
    )

    return ReviewChecklist(
        checklist_id="general_information",
        plan_type="project_narrative",
        section_id="general_information",
        title="GENERAL INFORMATION",
        description="General project and applicant information.",
        items=[item],
    )


def test_score_query_against_package_finding_matches_expected_terms():
    checklist = make_general_information_checklist()
    query = build_checklist_row_retrieval_query(
        checklist=checklist,
        item=checklist.items[0],
    )

    finding = {
        "item_id": "permit_activities_listing",
        "label": "Environmental permits",
        "finding": (
            "The project narrative lists activities requiring UIC, NPDES, "
            "and PSD permits."
        ),
        "matched_terms": ["UIC", "NPDES", "PSD"],
        "confidence": "High",
    }

    assert score_query_against_package_finding(query, finding) >= 5


def test_populate_checklist_row_from_query_uses_best_package_finding():
    checklist = make_general_information_checklist()
    query = build_checklist_row_retrieval_query(
        checklist=checklist,
        item=checklist.items[0],
    )

    package_findings = [
        {
            "item_id": "unrelated",
            "label": "Unrelated evidence",
            "finding": "This finding discusses something else.",
            "confidence": "Low",
        },
        {
            "item_id": "permit_activities_listing",
            "label": "Environmental permits",
            "finding": (
                "The project narrative lists activities requiring UIC, "
                "NPDES, and PSD permits."
            ),
            "confidence": "High",
            "matched_terms": ["UIC", "NPDES", "PSD"],
            "evidence_locations": [
                {
                    "file_name": "Project_Narrative.pdf",
                    "page_number": 12,
                    "excerpt": (
                        "The applicant lists activities requiring UIC, "
                        "NPDES, and PSD permits."
                    ),
                }
            ],
        },
    ]

    row = populate_checklist_row_from_query(
        query=query,
        package_findings=package_findings,
    )

    row_dict = row.to_dict()

    assert row.status == ChecklistPopulationStatus.PRESENT
    assert row_dict["file_name"] == "Project_Narrative.pdf"
    assert row_dict["page_number"] == 12
    assert "UIC" in row_dict["evidence_excerpt"]
    assert row_dict["confidence"] == "High"
    assert row_dict["reviewer_confirmation"] == "pending_review"


def test_populate_checklist_row_missing_when_no_package_finding_matches():
    checklist = make_general_information_checklist()
    query = build_checklist_row_retrieval_query(
        checklist=checklist,
        item=checklist.items[0],
    )

    row = populate_checklist_row_from_query(
        query=query,
        package_findings=[],
    )

    assert row.status == ChecklistPopulationStatus.MISSING
    assert row.file_name == ""
    assert row.page_number is None
    assert "No matching package review evidence" in row.system_notes


def test_infer_checklist_population_status_from_redacted_finding():
    finding = {
        "label": "Maximum injection pressure",
        "finding": (
            "The maximum injection pressure value is redacted in the public "
            "version of the application."
        ),
        "supporting_excerpts": [
            "Maximum injection pressure: [REDACTED] psi."
        ],
    }

    assert infer_checklist_population_status_from_finding(finding) == (
        ChecklistPopulationStatus.REDACTED
    )


def test_collect_package_review_findings_from_document_reviews():
    package_report = {
        "document_reviews": [
            {
                "document_name": "Project_Narrative.pdf",
                "checklist_reports": {
                    "project_narrative": {
                        "findings": [
                            {
                                "item_id": "permit_activities_listing",
                                "label": "Environmental permits",
                                "finding": "Permit listing is present.",
                            }
                        ]
                    }
                },
            }
        ]
    }

    findings = collect_package_review_findings_for_population(package_report)

    assert len(findings) == 1
    assert findings[0]["document_name"] == "Project_Narrative.pdf"
    assert findings[0]["item_id"] == "permit_activities_listing"


def test_build_populated_checklist_from_package_report_builds_section_summary():
    checklist = make_general_information_checklist()

    package_report = {
        "document_reviews": [
            {
                "document_name": "Project_Narrative.pdf",
                "checklist_reports": {
                    "project_narrative": {
                        "findings": [
                            {
                                "item_id": "permit_activities_listing",
                                "label": "Environmental permits",
                                "finding": (
                                    "The project narrative lists activities "
                                    "requiring UIC and NPDES permits."
                                ),
                                "matched_terms": ["UIC", "NPDES"],
                                "confidence": "High",
                                "evidence_locations": [
                                    {
                                        "file_name": "Project_Narrative.pdf",
                                        "page_number": 12,
                                        "excerpt": (
                                            "Activities require UIC and NPDES "
                                            "permits."
                                        ),
                                    }
                                ],
                            }
                        ]
                    }
                },
            }
        ]
    }

    checklist_output = build_populated_checklist_from_package_report(
        package_name="uploaded_package",
        checklists=[checklist],
        package_report=package_report,
    )

    checklist_dict = checklist_output.to_dict()

    assert checklist_dict["package_name"] == "uploaded_package"
    assert len(checklist_dict["rows"]) == 1
    assert checklist_dict["rows"][0]["status"] == "present"
    assert checklist_dict["section_summaries"][0]["section_title"] == (
        "GENERAL INFORMATION"
    )
    assert checklist_output.section_summaries[0].status == (
        ChecklistSectionStatus.GREEN
    )