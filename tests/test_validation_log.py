from review.validation_log import (
    ValidationFinding,
    normalize_validation_label,
    summarize_validation_findings,
    validation_summary_to_markdown,
)


def test_normalize_validation_label_accepts_known_label():
    assert normalize_validation_label("false-positive") == "false_positive"
    assert normalize_validation_label("OCR Issue") == "ocr_issue"


def test_normalize_validation_label_defaults_unknown_to_needs_review():
    assert normalize_validation_label("something unexpected") == "needs_review"


def test_summarize_validation_findings_counts_labels_and_follow_up():
    findings = [
        ValidationFinding(
            topic="Injection pressure monitoring",
            system_status="present",
            reviewer_status="present",
            label="pass",
        ),
        ValidationFinding(
            topic="Annular pressure monitoring",
            system_status="present",
            reviewer_status="evidence_found",
            label="overcredited",
            follow_up="Tighten evidence group requirements.",
        ),
        ValidationFinding(
            topic="Redacted OCR page",
            system_status="evidence_found",
            reviewer_status="needs_review",
            label="ocr_issue",
            follow_up="Confirm redacted OCR warning appears.",
        ),
    ]

    summary = summarize_validation_findings(findings)

    assert summary.total_findings == 3
    assert summary.label_counts["pass"] == 1
    assert summary.label_counts["overcredited"] == 1
    assert summary.label_counts["ocr_issue"] == 1
    assert summary.requires_follow_up is True
    assert "synthetic regression tests" in summary.recommended_next_action


def test_summarize_validation_findings_without_issues_passes():
    findings = [
        ValidationFinding(
            topic="Injection pressure monitoring",
            system_status="present",
            reviewer_status="present",
            label="pass",
        )
    ]

    summary = summarize_validation_findings(findings)

    assert summary.requires_follow_up is False
    assert "Validation passed" in summary.recommended_next_action


def test_validation_summary_to_markdown_renders_counts():
    findings = [
        ValidationFinding(
            topic="Classification",
            system_status="testing_monitoring",
            reviewer_status="testing_monitoring",
            label="pass",
        ),
        ValidationFinding(
            topic="Page location",
            system_status="page 4",
            reviewer_status="page 5",
            label="page_location_issue",
        ),
    ]

    summary = summarize_validation_findings(findings)
    markdown = validation_summary_to_markdown(summary)

    assert "## Validation Summary" in markdown
    assert "**Total findings:** 2" in markdown
    assert "`pass`" in markdown
    assert "`page_location_issue`" in markdown