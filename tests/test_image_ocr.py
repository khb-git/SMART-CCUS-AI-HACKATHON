from review.image_ocr import (
    IMAGE_OCR_SOURCE_TYPE,
    REDACTED_IMAGE_OCR_SOURCE_TYPE,
    build_image_ocr_result,
    classify_ocr_source_type,
    contains_redaction_marker,
    image_ocr_results_to_chunks,
    normalize_ocr_text,
)


def test_normalize_ocr_text_collapses_whitespace():
    assert normalize_ocr_text("  Figure   2-1\n\nAoR   Map  ") == "Figure 2-1 AoR Map"


def test_contains_redaction_marker_detects_confidential_text():
    assert contains_redaction_marker(
        "Sensitive, Confidential, or Privileged Information"
    )


def test_classify_ocr_source_type_returns_redacted_for_confidential_text():
    assert (
        classify_ocr_source_type("Sensitive Confidential Information")
        == REDACTED_IMAGE_OCR_SOURCE_TYPE
    )


def test_classify_ocr_source_type_returns_image_ocr_for_visible_text():
    assert classify_ocr_source_type("Figure 2-1 Area of Review Map") == IMAGE_OCR_SOURCE_TYPE


def test_build_image_ocr_result_ignores_empty_text():
    assert build_image_ocr_result(page_number=1, text="   \n ") is None


def test_build_image_ocr_result_labels_redacted_image_ocr():
    result = build_image_ocr_result(
        page_number=3,
        text="Sensitive, Confidential, or Privileged Information",
    )

    assert result is not None
    assert result.page_number == 3
    assert result.source_type == REDACTED_IMAGE_OCR_SOURCE_TYPE
    assert result.redaction_detected is True
    assert "Sensitive" in result.text


def test_image_ocr_results_to_chunks_preserves_source_metadata():
    result = build_image_ocr_result(
        page_number=4,
        text="Figure 2-1 Area of Review Map showing monitoring wells",
    )

    chunks = image_ocr_results_to_chunks(
        [result],
        file_name="aor_plan.pdf",
    )

    assert chunks == [
        {
            "text": "Figure 2-1 Area of Review Map showing monitoring wells",
            "metadata": {
                "file_name": "aor_plan.pdf",
                "page_number": 4,
                "chunk_index": 0,
                "content_type": IMAGE_OCR_SOURCE_TYPE,
                "source_type": IMAGE_OCR_SOURCE_TYPE,
                "redaction_detected": False,
                "ocr_confidence": "Low",
                "reviewer_note": (
                    "This evidence was extracted from image/OCR content "
                    "and should be verified against the source page."
                ),
            },
        }
    ]