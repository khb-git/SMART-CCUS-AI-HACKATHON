def test_aor_corrective_action_checklist_includes_expanded_epa_guidance_items():
    from review.schema import load_default_checklist

    checklist = load_default_checklist("aor_corrective_action")
    item_ids = {item.item_id for item in checklist.items}

    expected_item_ids = {
        "model_input_parameters",
        "model_calibration_validation",
        "uncertainty_sensitivity_analysis",
        "artificial_penetration_evaluation",
        "phased_corrective_action",
    }

    assert expected_item_ids.issubset(item_ids)


def test_aor_corrective_action_expanded_evidence_groups_load():
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("aor_corrective_action")

    model_inputs = get_checklist_item(checklist, "model_input_parameters")
    uncertainty = get_checklist_item(checklist, "uncertainty_sensitivity_analysis")
    penetrations = get_checklist_item(checklist, "artificial_penetration_evaluation")

    assert "geologic_properties" in model_inputs.evidence_groups
    assert "intrinsic permeability" in model_inputs.evidence_groups["geologic_properties"]

    assert "sensitivity" in uncertainty.evidence_groups
    assert "sensitivity analysis" in uncertainty.evidence_groups["sensitivity"]

    assert "integrity_evaluation" in penetrations.evidence_groups
    assert "plugging records" in penetrations.evidence_groups["integrity_evaluation"]