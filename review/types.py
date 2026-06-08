"""
Shared types for document review checklists.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ReviewSeverity(str, Enum):
    """Severity levels for missing or weak review items."""

    CRITICAL = "critical"
    MODERATE = "moderate"
    MINOR = "minor"


class ReviewRequirementLevel(str, Enum):
    """Whether a checklist item is required or optional."""

    REQUIRED = "required"
    RECOMMENDED = "recommended"
    OPTIONAL = "optional"


@dataclass
class ReviewChecklistItem:
    """One item that should be checked in a review document."""

    item_id: str
    label: str
    description: str
    requirement_level: ReviewRequirementLevel
    severity: ReviewSeverity
    expected_evidence_terms: list[str] = field(default_factory=list)
    evidence_groups: dict[str, list[str]] = field(default_factory=dict)
    reference_queries: list[str] = field(default_factory=list)
    permit_precedent_queries: list[str] = field(default_factory=list)
    recommended_fix: str = ""

    def to_dict(self):
        """Return JSON-serializable item data."""
        return {
            "item_id": self.item_id,
            "label": self.label,
            "description": self.description,
            "requirement_level": self.requirement_level.value,
            "severity": self.severity.value,
            "expected_evidence_terms": self.expected_evidence_terms,
            "evidence_groups": self.evidence_groups,
            "reference_queries": self.reference_queries,
            "permit_precedent_queries": self.permit_precedent_queries,
            "recommended_fix": self.recommended_fix,
        }


@dataclass
class ReviewChecklist:
    """Checklist for one plan/document type."""

    checklist_id: str
    plan_type: str
    section_id: str
    title: str
    description: str
    items: list[ReviewChecklistItem]

    def required_items(self) -> list[ReviewChecklistItem]:
        """Return required checklist items."""
        return [
            item
            for item in self.items
            if item.requirement_level == ReviewRequirementLevel.REQUIRED
        ]

    def to_dict(self):
        """Return JSON-serializable checklist data."""
        return {
            "checklist_id": self.checklist_id,
            "plan_type": self.plan_type,
            "section_id": self.section_id,
            "title": self.title,
            "description": self.description,
            "items": [item.to_dict() for item in self.items],
        }