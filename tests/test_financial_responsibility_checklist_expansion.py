def test_financial_responsibility_checklist_includes_expanded_cost_coverage_items():
    from review.schema import load_default_checklist

    checklist = load_default_checklist("financial_responsibility")
    item_ids = {item.item_id for item in checklist.items}

    expected_item_ids = {
        "corrective_action_cost_coverage",
        "injection_well_plugging_cost_coverage",
        "pisc_site_closure_cost_coverage",
        "emergency_remedial_response_cost_coverage",
        "instrument_update_replacement",
    }

    assert expected_item_ids.issubset(item_ids)


def test_financial_responsibility_expanded_evidence_groups_load():
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("financial_responsibility")

    corrective_action = get_checklist_item(
        checklist,
        "corrective_action_cost_coverage",
    )
    plugging = get_checklist_item(
        checklist,
        "injection_well_plugging_cost_coverage",
    )
    instrument_update = get_checklist_item(
        checklist,
        "instrument_update_replacement",
    )

    assert "aor_basis" in corrective_action.evidence_groups
    assert "artificial penetrations" in corrective_action.evidence_groups["aor_basis"]

    assert "plugging_activity" in plugging.evidence_groups
    assert "cement plug" in plugging.evidence_groups["plugging_activity"]

    assert "cancellation_expiration" in instrument_update.evidence_groups
    assert "expiration" in instrument_update.evidence_groups["cancellation_expiration"]