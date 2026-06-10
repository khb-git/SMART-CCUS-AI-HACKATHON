def test_pisc_site_closure_checklist_includes_expanded_items():
    from review.schema import load_default_checklist

    checklist = load_default_checklist("pisc_site_closure")
    item_ids = {item.item_id for item in checklist.items}

    expected_item_ids = {
        "pisc_monitoring_program",
        "alternative_pisc_timeframe",
        "site_closure_report_contents",
        "pisc_financial_responsibility_linkage",
        "post_closure_notice_records",
    }

    assert expected_item_ids.issubset(item_ids)


def test_pisc_site_closure_expanded_evidence_groups_load():
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("pisc_site_closure")

    monitoring = get_checklist_item(
        checklist,
        "pisc_monitoring_program",
    )
    alternative_timeframe = get_checklist_item(
        checklist,
        "alternative_pisc_timeframe",
    )
    post_closure_records = get_checklist_item(
        checklist,
        "post_closure_notice_records",
    )

    assert "monitoring_types" in monitoring.evidence_groups
    assert "groundwater monitoring" in monitoring.evidence_groups["monitoring_types"]

    assert "technical_basis" in alternative_timeframe.evidence_groups
    assert "plume stabilization" in alternative_timeframe.evidence_groups["technical_basis"]

    assert "record_system" in post_closure_records.evidence_groups
    assert "property records" in post_closure_records.evidence_groups["record_system"]