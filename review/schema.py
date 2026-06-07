"""
Checklist loading and validation for document review workflows.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from review.types import (
    ReviewChecklist,
    ReviewChecklistItem,
    ReviewRequirementLevel,
    ReviewSeverity,
)


DEFAULT_CHECKLIST_DIR = Path(__file__).parent / "checklists"


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file into a dictionary."""
    path = Path(path)

    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError(f"Checklist YAML must contain a dictionary: {path}")

    return data


def parse_requirement_level(value: str) -> ReviewRequirementLevel:
    """Parse requirement level from string."""
    try:
        return ReviewRequirementLevel(str(value).lower())
    except ValueError as exc:
        raise ValueError(f"Unsupported requirement level: {value}") from exc


def parse_severity(value: str) -> ReviewSeverity:
    """Parse severity from string."""
    try:
        return ReviewSeverity(str(value).lower())
    except ValueError as exc:
        raise ValueError(f"Unsupported review severity: {value}") from exc


def build_checklist_item(data: dict[str, Any]) -> ReviewChecklistItem:
    """Build a checklist item from YAML data."""
    required_fields = [
        "item_id",
        "label",
        "description",
        "requirement_level",
        "severity",
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Checklist item missing required field: {field}")

    return ReviewChecklistItem(
        item_id=str(data["item_id"]),
        label=str(data["label"]),
        description=str(data["description"]),
        requirement_level=parse_requirement_level(data["requirement_level"]),
        severity=parse_severity(data["severity"]),
        expected_evidence_terms=list(data.get("expected_evidence_terms", [])),
        reference_queries=list(data.get("reference_queries", [])),
        permit_precedent_queries=list(data.get("permit_precedent_queries", [])),
        recommended_fix=str(data.get("recommended_fix", "")),
    )


def build_checklist(data: dict[str, Any]) -> ReviewChecklist:
    """Build a ReviewChecklist from YAML data."""
    required_fields = [
        "checklist_id",
        "plan_type",
        "section_id",
        "title",
        "description",
        "items",
    ]

    for field in required_fields:
        if field not in data:
            raise ValueError(f"Checklist missing required field: {field}")

    raw_items = data["items"]

    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("Checklist must contain at least one item.")

    items = [build_checklist_item(item) for item in raw_items]

    return ReviewChecklist(
        checklist_id=str(data["checklist_id"]),
        plan_type=str(data["plan_type"]),
        section_id=str(data["section_id"]),
        title=str(data["title"]),
        description=str(data["description"]),
        items=items,
    )


def load_checklist(path: str | Path) -> ReviewChecklist:
    """Load a checklist YAML file."""
    data = load_yaml(path)
    return build_checklist(data)


def load_default_checklist(plan_type: str) -> ReviewChecklist:
    """Load a default checklist by plan type."""
    checklist_path = DEFAULT_CHECKLIST_DIR / f"{plan_type}.yaml"

    if not checklist_path.exists():
        raise FileNotFoundError(f"No default checklist found for plan type: {plan_type}")

    return load_checklist(checklist_path)


def get_checklist_item(checklist: ReviewChecklist, item_id: str) -> ReviewChecklistItem:
    """Return one checklist item by ID."""
    for item in checklist.items:
        if item.item_id == item_id:
            return item

    raise KeyError(f"Checklist item not found: {item_id}")