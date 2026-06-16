import pytest

from review.gap_analysis import GapStatus, analyze_checklist_item
from review.types import (
    ReviewChecklistItem,
    ReviewRequirementLevel,
    ReviewSeverity,
)


def make_test_item() -> ReviewChecklistItem:
    return ReviewChecklistItem(
        item_id="injection_pressure_monitoring",
        label="Injection pressure monitoring",
        description="Confirm the plan describes injection pressure monitoring.",
        requirement_level=ReviewRequirementLevel.REQUIRED,
        severity=ReviewSeverity.MODERATE,
        expected_evidence_terms=[
            "injection pressure",
            "wellhead pressure",
            "pressure transducer",
        ],
        evidence_groups={},
        recommended_fix="Add injection pressure monitoring details.",
    )


def test_analyze_checklist_item_supports_text_only_call():
    item = make_test_item()
    finding = analyze_checklist_item(
        "The plan includes injection pressure and wellhead pressure monitoring.",
        item,
    )

    assert finding.item_id == "injection_pressure_monitoring"
    assert finding.status in {GapStatus.PRESENT, GapStatus.PARTIAL}
    assert "injection pressure" in finding.matched_terms
    assert finding.evidence_locations == []


def test_analyze_checklist_item_document_argument_is_keyword_only():
    item = make_test_item()

    with pytest.raises(TypeError):
        analyze_checklist_item(
            object(),
            "The plan includes injection pressure monitoring.",
            item,
        )