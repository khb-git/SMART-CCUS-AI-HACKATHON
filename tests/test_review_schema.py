from pathlib import Path


def test_load_default_testing_monitoring_checklist():
    from review.schema import load_default_checklist

    checklist = load_default_checklist("testing_monitoring")

    assert checklist.checklist_id == "testing_monitoring_v1"
    assert checklist.plan_type == "testing_monitoring"
    assert checklist.section_id == "8"
    assert checklist.title == "Testing and Monitoring Plan Checklist"
    assert len(checklist.items) >= 10


def test_testing_monitoring_checklist_has_core_items():
    from review.schema import load_default_checklist

    checklist = load_default_checklist("testing_monitoring")
    item_ids = {item.item_id for item in checklist.items}

    assert "injection_pressure_monitoring" in item_ids
    assert "injection_rate_monitoring" in item_ids
    assert "annular_pressure_monitoring" in item_ids
    assert "monitoring_frequency" in item_ids
    assert "calibration_schedule" in item_ids


def test_required_items_returns_only_required_items():
    from review.schema import load_default_checklist
    from review.types import ReviewRequirementLevel

    checklist = load_default_checklist("testing_monitoring")
    required_items = checklist.required_items()

    assert required_items
    assert all(
        item.requirement_level == ReviewRequirementLevel.REQUIRED
        for item in required_items
    )


def test_get_checklist_item_returns_expected_item():
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("testing_monitoring")
    item = get_checklist_item(checklist, "injection_pressure_monitoring")

    assert item.label == "Injection pressure monitoring"
    assert "pressure transducer" in item.expected_evidence_terms
    assert item.severity.value == "critical"


def test_get_checklist_item_raises_for_missing_item():
    import pytest

    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("testing_monitoring")

    with pytest.raises(KeyError):
        get_checklist_item(checklist, "not_a_real_item")


def test_load_checklist_rejects_missing_required_fields(tmp_path):
    import pytest

    from review.schema import load_checklist

    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text(
        """
plan_type: testing_monitoring
section_id: "8"
items: []
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_checklist(bad_yaml)


def test_checklist_to_dict_is_serializable():
    from review.schema import load_default_checklist

    checklist = load_default_checklist("testing_monitoring")
    data = checklist.to_dict()

    assert data["checklist_id"] == "testing_monitoring_v1"
    assert data["items"]
    assert data["items"][0]["item_id"]
    assert data["items"][0]["requirement_level"] in {
        "required",
        "recommended",
        "optional",
    }

def test_build_checklist_item_loads_evidence_groups():
    from review.schema import build_checklist_item

    item = build_checklist_item(
        {
            "item_id": "injection_pressure_monitoring",
            "label": "Injection pressure monitoring",
            "description": "Document should describe pressure monitoring.",
            "requirement_level": "required",
            "severity": "critical",
            "expected_evidence_terms": ["injection pressure", "SCADA"],
            "evidence_groups": {
                "parameter": ["injection pressure"],
                "recording": ["SCADA"],
            },
        }
    )

    assert item.evidence_groups == {
        "parameter": ["injection pressure"],
        "recording": ["SCADA"],
    }