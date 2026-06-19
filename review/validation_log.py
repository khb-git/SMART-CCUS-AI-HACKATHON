"""
Utilities for sanitized real-document validation logs.

These helpers intentionally operate on reviewer-entered validation notes rather
than raw permit documents. They support consistent validation summaries without
committing sensitive source material.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


VALIDATION_LABELS = {
    "pass",
    "needs_review",
    "false_positive",
    "false_negative",
    "overcredited",
    "undercredited",
    "ocr_issue",
    "page_location_issue",
    "classification_issue",
    "known_limitation",
}


@dataclass(frozen=True)
class ValidationFinding:
    """One sanitized validation observation."""

    topic: str
    system_status: str
    reviewer_status: str
    label: str
    note: str = ""
    follow_up: str = ""


@dataclass(frozen=True)
class ValidationSummary:
    """Summary of sanitized validation findings."""

    total_findings: int
    label_counts: dict[str, int] = field(default_factory=dict)
    requires_follow_up: bool = False
    recommended_next_action: str = ""


def normalize_validation_label(label: str) -> str:
    """Normalize and validate a validation label."""
    normalized = str(label or "").strip().lower().replace(" ", "_").replace("-", "_")

    if normalized not in VALIDATION_LABELS:
        return "needs_review"

    return normalized


def summarize_validation_findings(
    findings: list[ValidationFinding],
) -> ValidationSummary:
    """Summarize sanitized real-document validation findings."""
    normalized_labels = [
        normalize_validation_label(finding.label)
        for finding in findings
    ]

    label_counts = dict(Counter(normalized_labels))

    follow_up_labels = {
        "needs_review",
        "false_positive",
        "false_negative",
        "overcredited",
        "undercredited",
        "ocr_issue",
        "page_location_issue",
        "classification_issue",
        "known_limitation",
    }

    requires_follow_up = any(label in follow_up_labels for label in normalized_labels)

    if not findings:
        recommended_next_action = (
            "Run a real-document validation review and record sanitized findings."
        )
    elif requires_follow_up:
        recommended_next_action = (
            "Convert repeatable validation issues into synthetic regression tests "
            "or checklist/rule updates."
        )
    else:
        recommended_next_action = (
            "Validation passed. Preserve the sanitized log and proceed with final "
            "reviewer/demo checks."
        )

    return ValidationSummary(
        total_findings=len(findings),
        label_counts=label_counts,
        requires_follow_up=requires_follow_up,
        recommended_next_action=recommended_next_action,
    )


def validation_summary_to_markdown(summary: ValidationSummary) -> str:
    """Render a validation summary as Markdown."""
    lines = [
        "## Validation Summary",
        "",
        f"- **Total findings:** {summary.total_findings}",
        f"- **Requires follow-up:** {'Yes' if summary.requires_follow_up else 'No'}",
        f"- **Recommended next action:** {summary.recommended_next_action}",
        "",
        "| Label | Count |",
        "| --- | ---: |",
    ]

    if summary.label_counts:
        for label, count in sorted(summary.label_counts.items()):
            lines.append(f"| `{label}` | {count} |")
    else:
        lines.append("| None | 0 |")

    return "\n".join(lines) + "\n"