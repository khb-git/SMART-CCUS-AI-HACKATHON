"""
Utilities for converting sanitized validation findings into regression candidates.

These helpers do not use real permit text. They operate on reviewer-entered,
sanitized validation findings and produce structured candidates for future
synthetic regression tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from review.validation_log import ValidationFinding, normalize_validation_label


REGRESSION_WORTHY_LABELS = {
    "false_positive",
    "false_negative",
    "overcredited",
    "undercredited",
    "ocr_issue",
    "page_location_issue",
    "classification_issue",
}


LABEL_TO_TEST_FOCUS = {
    "false_positive": "prevent over-crediting unsupported evidence",
    "false_negative": "detect evidence that was previously missed",
    "overcredited": "tighten checklist satisfaction requirements",
    "undercredited": "avoid unnecessary missing or evidence-found status",
    "ocr_issue": "preserve OCR source labels and reviewer warnings",
    "page_location_issue": "preserve accurate evidence page locations",
    "classification_issue": "improve document classification behavior",
}


@dataclass(frozen=True)
class RegressionCandidate:
    """One sanitized candidate for a future synthetic regression test."""

    topic: str
    validation_label: str
    test_focus: str
    system_status: str
    reviewer_status: str
    sanitized_note: str = ""
    suggested_test_name: str = ""
    follow_up: str = ""


def slugify_test_name(value: str) -> str:
    """Return a safe snake_case value for a pytest function name."""
    cleaned = []
    previous_was_underscore = False

    for char in str(value or "").lower():
        if char.isalnum():
            cleaned.append(char)
            previous_was_underscore = False
        elif not previous_was_underscore:
            cleaned.append("_")
            previous_was_underscore = True

    slug = "".join(cleaned).strip("_")

    return slug or "validation_issue"


def is_regression_worthy(finding: ValidationFinding) -> bool:
    """Return whether a validation finding should become a regression candidate."""
    return normalize_validation_label(finding.label) in REGRESSION_WORTHY_LABELS


def build_suggested_test_name(finding: ValidationFinding) -> str:
    """Build a readable pytest-style function name for a regression candidate."""
    label = normalize_validation_label(finding.label)
    topic_slug = slugify_test_name(finding.topic)

    return f"test_validation_{label}_{topic_slug}"


def validation_finding_to_regression_candidate(
    finding: ValidationFinding,
) -> RegressionCandidate | None:
    """Convert one sanitized validation finding into a regression candidate."""
    label = normalize_validation_label(finding.label)

    if label not in REGRESSION_WORTHY_LABELS:
        return None

    return RegressionCandidate(
        topic=finding.topic,
        validation_label=label,
        test_focus=LABEL_TO_TEST_FOCUS[label],
        system_status=finding.system_status,
        reviewer_status=finding.reviewer_status,
        sanitized_note=finding.note,
        suggested_test_name=build_suggested_test_name(finding),
        follow_up=finding.follow_up,
    )


def collect_regression_candidates(
    findings: list[ValidationFinding],
) -> list[RegressionCandidate]:
    """Collect regression candidates from sanitized validation findings."""
    candidates = []

    for finding in findings:
        candidate = validation_finding_to_regression_candidate(finding)

        if candidate is not None:
            candidates.append(candidate)

    return candidates


def regression_candidates_to_markdown(
    candidates: list[RegressionCandidate],
) -> str:
    """Render regression candidates as a Markdown table."""
    lines = [
        "## Regression Test Candidates",
        "",
        (
            "These candidates are derived from sanitized validation findings. "
            "Use synthetic text only when implementing tests."
        ),
        "",
        "| Topic | Label | Test Focus | System Status | Reviewer Status | Suggested Test | Follow-Up |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    if not candidates:
        lines.append("| None | None | None | None | None | None | None |")
        return "\n".join(lines) + "\n"

    for candidate in candidates:
        lines.append(
            "| "
            + " | ".join(
                [
                    candidate.topic,
                    f"`{candidate.validation_label}`",
                    candidate.test_focus,
                    candidate.system_status,
                    candidate.reviewer_status,
                    f"`{candidate.suggested_test_name}`",
                    candidate.follow_up or "None",
                ]
            )
            + " |"
        )

    return "\n".join(lines) + "\n"