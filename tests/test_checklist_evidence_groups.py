def test_marquis_aligned_checklists_include_evidence_groups():
    from review.schema import load_default_checklist

    checklist_names = [
        "testing_monitoring",
        "well_construction",
        "financial_responsibility",
        "aor_corrective_action",
    ]

    for checklist_name in checklist_names:
        checklist = load_default_checklist(checklist_name)

        assert checklist.items

        required_items = [
            item
            for item in checklist.items
            if item.requirement_level.value == "required"
        ]

        assert required_items

        for item in required_items:
            assert item.evidence_groups, (
                f"{checklist_name}.{item.item_id} is missing evidence_groups"
            )


def test_testing_monitoring_pressure_groups_are_loaded():
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("testing_monitoring")
    item = get_checklist_item(checklist, "injection_pressure_monitoring")

    assert item.evidence_groups["parameter"]
    assert item.evidence_groups["equipment"]
    assert item.evidence_groups["frequency"]
    assert item.evidence_groups["location"]


def test_financial_responsibility_cost_groups_are_loaded():
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("financial_responsibility")
    item = get_checklist_item(checklist, "cost_estimate")

    assert item.evidence_groups["estimate"]
    assert item.evidence_groups["activity_costs"]