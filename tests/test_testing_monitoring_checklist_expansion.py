def test_testing_monitoring_checklist_includes_expanded_epa_guidance_items():
    from review.schema import load_default_checklist

    checklist = load_default_checklist("testing_monitoring")
    item_ids = {item.item_id for item in checklist.items}

    expected_item_ids = {
        "co2_stream_analysis",
        "groundwater_geochemical_monitoring",
        "plume_pressure_front_tracking",
        "mechanical_integrity_testing",
        "corrosion_monitoring",
        "surface_air_soil_gas_monitoring",
    }

    assert expected_item_ids.issubset(item_ids)


def test_testing_monitoring_expanded_evidence_groups_load():
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("testing_monitoring")

    groundwater = get_checklist_item(
        checklist,
        "groundwater_geochemical_monitoring",
    )
    plume_tracking = get_checklist_item(
        checklist,
        "plume_pressure_front_tracking",
    )
    mit = get_checklist_item(
        checklist,
        "mechanical_integrity_testing",
    )

    assert "monitoring_network" in groundwater.evidence_groups
    assert "monitoring wells" in groundwater.evidence_groups["monitoring_network"]

    assert "model_comparison" in plume_tracking.evidence_groups
    assert "model predictions" in plume_tracking.evidence_groups["model_comparison"]

    assert "external_mit" in mit.evidence_groups
    assert "radioactive tracer survey" in mit.evidence_groups["external_mit"]