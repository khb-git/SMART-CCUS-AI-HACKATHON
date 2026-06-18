from review.reviewer_disclaimers import (
    CORE_REVIEW_DISCLAIMER,
    OCR_REVIEW_DISCLAIMER,
    build_known_limitations_lines,
    build_reviewer_disclaimer_lines,
)


def test_build_reviewer_disclaimer_lines_mentions_reviewer_confirmation():
    markdown = "\n".join(build_reviewer_disclaimer_lines())

    assert "## Reviewer Disclaimers" in markdown
    assert CORE_REVIEW_DISCLAIMER in markdown
    assert "qualified reviewer" in markdown
    assert "not a final regulatory determination" in markdown


def test_build_reviewer_disclaimer_lines_mentions_ocr_redaction_boundary():
    markdown = "\n".join(build_reviewer_disclaimer_lines())

    assert OCR_REVIEW_DISCLAIMER in markdown
    assert "visible text only" in markdown
    assert "does not inspect, recover, or infer hidden content" in markdown


def test_build_known_limitations_lines_lists_core_boundaries():
    markdown = "\n".join(build_known_limitations_lines())

    assert "## Known Limitations" in markdown
    assert "deterministic rules" in markdown
    assert "OCR quality depends" in markdown
    assert "does not replace legal, engineering, or regulatory judgment" in markdown