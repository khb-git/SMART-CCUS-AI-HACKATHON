def test_emergency_remedial_response_checklist_includes_expanded_items():
    from review.schema import load_default_checklist

    checklist = load_default_checklist("emergency_remedial_response")
    item_ids = {item.item_id for item in checklist.items}

    expected_item_ids = {
        "emergency_scenario_planning",
        "usdws_protection_measures",
        "post_event_investigation_monitoring",
        "restart_resumption_criteria",
        "emergency_documentation_reporting",
    }

    assert expected_item_ids.issubset(item_ids)


def test_emergency_remedial_response_expanded_evidence_groups_load():
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("emergency_remedial_response")

    scenarios = get_checklist_item(
        checklist,
        "emergency_scenario_planning",
    )
    protection = get_checklist_item(
        checklist,
        "usdws_protection_measures",
    )
    restart = get_checklist_item(
        checklist,
        "restart_resumption_criteria",
    )

    assert "scenarios" in scenarios.evidence_groups
    assert "release scenario" in scenarios.evidence_groups["scenarios"]

    assert "protection_actions" in protection.evidence_groups
    assert "groundwater protection" in protection.evidence_groups["protection_actions"]

    assert "readiness" in restart.evidence_groups
    assert "mechanical integrity demonstrated" in restart.evidence_groups["readiness"]