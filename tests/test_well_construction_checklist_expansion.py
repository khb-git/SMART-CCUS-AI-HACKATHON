def test_well_construction_checklist_includes_expanded_epa_guidance_items():
    from review.schema import load_default_checklist

    checklist = load_default_checklist("well_construction")
    item_ids = {item.item_id for item in checklist.items}

    expected_item_ids = {
        "mechanical_integrity_design",
        "logging_workover_design",
        "downhole_stress_design",
        "cement_verification_acceptance",
        "shutoff_safety_systems",
    }

    assert expected_item_ids.issubset(item_ids)


def test_well_construction_expanded_evidence_groups_load():
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("well_construction")

    mechanical_integrity = get_checklist_item(
        checklist,
        "mechanical_integrity_design",
    )
    stress_design = get_checklist_item(
        checklist,
        "downhole_stress_design",
    )
    shutoff = get_checklist_item(
        checklist,
        "shutoff_safety_systems",
    )

    assert "containment" in mechanical_integrity.evidence_groups
    assert "injection zone" in mechanical_integrity.evidence_groups["containment"]

    assert "pressure_basis" in stress_design.evidence_groups
    assert "fracture pressure" in stress_design.evidence_groups["pressure_basis"]

    assert "safety_systems" in shutoff.evidence_groups
    assert "emergency shutdown" in shutoff.evidence_groups["safety_systems"]