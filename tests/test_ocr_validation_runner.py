from review.temp_ingestion import TemporaryReviewChunk


def test_summarize_ocr_chunks_returns_only_ocr_chunks():
    from scripts.validate_ocr_review_ingestion import summarize_ocr_chunks

    chunks = [
        TemporaryReviewChunk(
            text="Normal text layer evidence.",
            metadata={"content_type": "text", "page": 1},
        ),
        TemporaryReviewChunk(
            text="Figure 2-1 Area of Review Map",
            metadata={
                "content_type": "image_ocr",
                "source_type": "image_ocr",
                "page_number": 2,
                "ocr_confidence": "Low",
                "redaction_detected": False,
                "reviewer_note": "Verify against the source page.",
            },
        ),
    ]

    summaries = summarize_ocr_chunks(chunks)

    assert len(summaries) == 1
    assert summaries[0]["page_number"] == 2
    assert summaries[0]["source_type"] == "image_ocr"
    assert summaries[0]["redaction_detected"] is False
    assert summaries[0]["excerpt"] == "Figure 2-1 Area of Review Map"


def test_summarize_ocr_chunks_preserves_redacted_ocr_warning():
    from scripts.validate_ocr_review_ingestion import summarize_ocr_chunks

    chunks = [
        TemporaryReviewChunk(
            text="Sensitive, Confidential, or Privileged Information",
            metadata={
                "content_type": "redacted_image_ocr",
                "source_type": "redacted_image_ocr",
                "page_number": 5,
                "ocr_confidence": "Low",
                "redaction_detected": True,
                "reviewer_note": (
                    "OCR detected redaction/confidentiality markers. "
                    "The backend cannot inspect or infer hidden content."
                ),
            },
        ),
    ]

    summaries = summarize_ocr_chunks(chunks)

    assert len(summaries) == 1
    assert summaries[0]["source_type"] == "redacted_image_ocr"
    assert summaries[0]["redaction_detected"] is True
    assert "cannot inspect or infer hidden content" in summaries[0]["reviewer_note"]


def test_shorten_text_truncates_long_excerpts():
    from scripts.validate_ocr_review_ingestion import shorten_text

    long_text = " ".join(["Area of Review"] * 100)

    shortened = shorten_text(long_text, max_chars=80)

    assert shortened.endswith("...")
    assert len(shortened) <= 83