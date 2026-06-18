from review.checklist_population import (
    build_checklist_retrieval_queries,
    build_checklist_row_retrieval_query,
    citation_from_text,
    unique_nonempty_strings,
)
from review.types import (
    ReviewChecklist,
    ReviewChecklistItem,
    ReviewRequirementLevel,
    ReviewSeverity,
)


def make_test_checklist() -> ReviewChecklist:
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
        reference_queries=[
            "40 CFR 144.31(e)(1) permit application activities",
        ],
        permit_precedent_queries=[
            "activities requiring RCRA UIC NPDES PSD permits",
        ],
        recommended_fix=(
            "Locate the applicant's listing of regulated activities and permits."
        ),
    )

    return ReviewChecklist(
        checklist_id="general_information",
        plan_type="project_narrative",
        section_id="general_information",
        title="GENERAL INFORMATION",
        description="General project and applicant information.",
        items=[item],
    )


def test_unique_nonempty_strings_preserves_order_and_deduplicates():
    values = [
        "RCRA",
        "",
        "  UIC  ",
        "rcra",
        "NPDES\nPermit",
        "NPDES Permit",
    ]

    assert unique_nonempty_strings(values) == [
        "RCRA",
        "UIC",
        "NPDES Permit",
    ]


def test_citation_from_text_extracts_bracketed_cfr_citation():
    text = (
        "A listing of activities requiring permits. "
        "[40 CFR 144.31(e)(1)]"
    )

    assert citation_from_text(text) == "40 CFR 144.31(e)(1)"


def test_citation_from_text_ignores_non_cfr_brackets():
    assert citation_from_text("Optional item [not a citation]") == ""


def test_build_checklist_row_retrieval_query_uses_checklist_context():
    checklist = make_test_checklist()
    item = checklist.items[0]

    query = build_checklist_row_retrieval_query(
        checklist=checklist,
        item=item,
    )

    query_dict = query.to_dict()

    assert query.section_title == "GENERAL INFORMATION"
    assert query.checklist_item_id == "permit_activities_listing"
    assert query.expected_plan_type == "project_narrative"
    assert query.citation == "40 CFR 144.31(e)(1)"
    assert "GENERAL INFORMATION" in query.query_text
    assert "RCRA" in query.query_text
    assert "NPDES" in query.query_text
    assert "project narrative" in query.query_text
    assert "40 CFR 144.31(e)(1)" in query.required_terms
    assert "environmental permits" in query.optional_terms
    assert query.reference_queries == [
        "40 CFR 144.31(e)(1) permit application activities"
    ]
    assert query.permit_precedent_queries == [
        "activities requiring RCRA UIC NPDES PSD permits"
    ]
    assert query_dict["checklist_item_id"] == "permit_activities_listing"


def test_build_checklist_retrieval_queries_builds_one_query_per_item():
    checklist = make_test_checklist()

    queries = build_checklist_retrieval_queries(checklist)

    assert len(queries) == 1
    assert queries[0].checklist_item_id == "permit_activities_listing"
    assert queries[0].checklist_item.startswith("A listing of the activities")