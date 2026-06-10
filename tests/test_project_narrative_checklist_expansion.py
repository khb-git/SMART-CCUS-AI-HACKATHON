def test_project_narrative_checklist_includes_epa_general_information_items():
    from review.schema import load_default_checklist

    checklist = load_default_checklist("project_narrative")
    item_ids = {item.item_id for item in checklist.items}

    expected_item_ids = {
        "environmental_permit_activities",
        "facility_identity",
        "sic_codes",
        "operator_ownership_status",
        "indian_lands_status",
        "environmental_permits_and_approvals",
        "map_of_area",
        "aor_contacts",
    }

    assert expected_item_ids.issubset(item_ids)


def test_project_narrative_checklist_evidence_groups_load():
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("project_narrative")
    map_item = get_checklist_item(checklist, "map_of_area")
    operator_item = get_checklist_item(checklist, "operator_ownership_status")

    assert "required_features" in map_item.evidence_groups
    assert "injection well" in map_item.evidence_groups["required_features"]
    assert "ownership" in operator_item.evidence_groups
    assert "ownership status" in operator_item.evidence_groups["ownership"]