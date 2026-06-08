ADDITIONAL_PLAN_TYPES = [
    "pre_operational_testing",
    "pisc_site_closure",
    "emergency_remedial_response",
    "well_construction",
    "aor_corrective_action",
    "financial_responsibility",
    "site_operating",
    "site_geologic_characterization",
    "injection_well_plugging",
    "project_narrative",
]


def test_all_additional_review_checklists_load():
    from review.schema import load_default_checklist

    for plan_type in ADDITIONAL_PLAN_TYPES:
        checklist = load_default_checklist(plan_type)

        assert checklist.plan_type == plan_type
        assert checklist.checklist_id.endswith("_v1")
        assert checklist.section_id
        assert checklist.title
        assert checklist.description
        assert len(checklist.items) >= 5


def test_all_additional_review_checklists_have_required_items():
    from review.schema import load_default_checklist
    from review.types import ReviewRequirementLevel

    for plan_type in ADDITIONAL_PLAN_TYPES:
        checklist = load_default_checklist(plan_type)
        required_items = checklist.required_items()

        assert required_items
        assert all(
            item.requirement_level == ReviewRequirementLevel.REQUIRED
            for item in required_items
        )


def test_all_additional_review_checklist_items_have_review_fields():
    from review.schema import load_default_checklist

    for plan_type in ADDITIONAL_PLAN_TYPES:
        checklist = load_default_checklist(plan_type)

        for item in checklist.items:
            assert item.item_id
            assert item.label
            assert item.description
            assert item.severity.value in {"critical", "moderate", "minor"}
            assert item.requirement_level.value in {
                "required",
                "recommended",
                "optional",
            }
            assert item.expected_evidence_terms
            assert item.reference_queries
            assert item.permit_precedent_queries
            assert item.recommended_fix


def test_document_classifier_plan_types_have_matching_checklists():
    from review.document_classifier import DOCUMENT_TYPE_RULES
    from review.schema import load_default_checklist

    unsupported_for_now = set()

    for plan_type in DOCUMENT_TYPE_RULES:
        if plan_type in unsupported_for_now:
            continue

        checklist = load_default_checklist(plan_type)

        assert checklist.plan_type == plan_type