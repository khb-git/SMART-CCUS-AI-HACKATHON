def test_injection_well_plugging_checklist_includes_expanded_items():
    from review.schema import load_default_checklist

    checklist = load_default_checklist("injection_well_plugging")
    item_ids = {item.item_id for item in checklist.items}

    expected_item_ids = {
        "plugging_materials_design",
        "co2_compatibility_for_plugging",
        "plugging_schedule_notification",
        "post_plugging_site_condition",
        "plugging_records_retention",
    }

    assert expected_item_ids.issubset(item_ids)


def test_injection_well_plugging_expanded_evidence_groups_load():
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("injection_well_plugging")

    materials = get_checklist_item(
        checklist,
        "plugging_materials_design",
    )
    compatibility = get_checklist_item(
        checklist,
        "co2_compatibility_for_plugging",
    )
    records = get_checklist_item(
        checklist,
        "plugging_records_retention",
    )

    assert "performance" in materials.evidence_groups
    assert "compressive strength" in materials.evidence_groups["performance"]

    assert "fluids_conditions" in compatibility.evidence_groups
    assert "formation fluids" in compatibility.evidence_groups["fluids_conditions"]

    assert "documentation" in records.evidence_groups
    assert "as-built" in records.evidence_groups["documentation"]