from review.validation_log import ValidationFinding

from review.regression_candidates import (
    build_suggested_test_name,
    collect_regression_candidates,
    is_regression_worthy,
    regression_candidates_to_markdown,
    slugify_test_name,
    validation_finding_to_regression_candidate,
)


def test_slugify_test_name_returns_safe_snake_case():
    assert slugify_test_name("Annular Pressure Monitoring!") == "annular_pressure_monitoring"
    assert slugify_test_name("OCR / Redacted Page #3") == "ocr_redacted_page_3"


def test_is_regression_worthy_accepts_issue_labels():
    finding = ValidationFinding(
        topic="Injection pressure monitoring",
        system_status="present",
        reviewer_status="evidence_found",
        label="overcredited",
    )

    assert is_regression_worthy(finding) is True


def test_is_regression_worthy_skips_pass_label():
    finding = ValidationFinding(
        topic="Injection pressure monitoring",
        system_status="present",
        reviewer_status="present",
        label="pass",
    )

    assert is_regression_worthy(finding) is False


def test_build_suggested_test_name_uses_label_and_topic():
    finding = ValidationFinding(
        topic="Annular pressure monitoring",
        system_status="present",
        reviewer_status="evidence_found",
        label="overcredited",
    )

    assert (
        build_suggested_test_name(finding)
        == "test_validation_overcredited_annular_pressure_monitoring"
    )


def test_validation_finding_to_regression_candidate_maps_issue():
    finding = ValidationFinding(
        topic="Redacted OCR evidence",
        system_status="evidence_found",
        reviewer_status="needs_review",
        label="ocr_issue",
        note="OCR warning was not visible enough.",
        follow_up="Strengthen OCR warning display.",
    )

    candidate = validation_finding_to_regression_candidate(finding)

    assert candidate is not None
    assert candidate.topic == "Redacted OCR evidence"
    assert candidate.validation_label == "ocr_issue"
    assert candidate.test_focus == "preserve OCR source labels and reviewer warnings"
    assert candidate.suggested_test_name == "test_validation_ocr_issue_redacted_ocr_evidence"
    assert candidate.follow_up == "Strengthen OCR warning display."


def test_validation_finding_to_regression_candidate_skips_pass():
    finding = ValidationFinding(
        topic="Classification",
        system_status="testing_monitoring",
        reviewer_status="testing_monitoring",
        label="pass",
    )

    assert validation_finding_to_regression_candidate(finding) is None


def test_collect_regression_candidates_filters_non_issues():
    findings = [
        ValidationFinding(
            topic="Classification",
            system_status="testing_monitoring",
            reviewer_status="testing_monitoring",
            label="pass",
        ),
        ValidationFinding(
            topic="Artificial penetrations",
            system_status="missing",
            reviewer_status="present",
            label="false_negative",
        ),
        ValidationFinding(
            topic="Page location",
            system_status="page 4",
            reviewer_status="page 5",
            label="page_location_issue",
        ),
    ]

    candidates = collect_regression_candidates(findings)

    assert len(candidates) == 2
    assert candidates[0].validation_label == "false_negative"
    assert candidates[1].validation_label == "page_location_issue"


def test_regression_candidates_to_markdown_renders_table():
    findings = [
        ValidationFinding(
            topic="Financial responsibility instrument",
            system_status="present",
            reviewer_status="evidence_found",
            label="overcredited",
            follow_up="Require payable-to evidence group.",
        )
    ]

    candidates = collect_regression_candidates(findings)
    markdown = regression_candidates_to_markdown(candidates)

    assert "## Regression Test Candidates" in markdown
    assert "Financial responsibility instrument" in markdown
    assert "`overcredited`" in markdown
    assert "`test_validation_overcredited_financial_responsibility_instrument`" in markdown
    assert "Require payable-to evidence group." in markdown


def test_regression_candidates_to_markdown_handles_empty_candidates():
    markdown = regression_candidates_to_markdown([])

    assert "## Regression Test Candidates" in markdown
    assert "| None | None | None | None | None | None | None |" in markdown