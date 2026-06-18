"""
Image/OCR evidence extraction helpers.

This module provides a safe OCR-first layer for image-only or low-text PDF pages.
It extracts visible text only. It does not infer hidden or redacted content.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable

import fitz
import pytesseract
from PIL import Image


IMAGE_OCR_SOURCE_TYPE = "image_ocr"
REDACTED_IMAGE_OCR_SOURCE_TYPE = "redacted_image_ocr"

REDACTION_MARKERS = (
    "redacted",
    "confidential",
    "privileged",
    "sensitive",
    "withheld",
    "not for public disclosure",
    "proprietary",
    "trade secret",
    "cbi",
    "confidential business information",
)


@dataclass(frozen=True)
class ImageOcrResult:
    """OCR text extracted from one rendered document page."""

    page_number: int
    text: str
    source_type: str = IMAGE_OCR_SOURCE_TYPE
    redaction_detected: bool = False
    confidence: str = "Low"


def normalize_ocr_text(value: str) -> str:
    """Normalize OCR text for matching and storage."""
    return " ".join(str(value or "").split()).strip()


def contains_redaction_marker(text: str) -> bool:
    """Return whether OCR text contains redaction/confidentiality markers."""
    normalized = normalize_ocr_text(text).lower()

    return any(marker in normalized for marker in REDACTION_MARKERS)


def classify_ocr_source_type(text: str) -> str:
    """Return OCR evidence source type based on redaction markers."""
    if contains_redaction_marker(text):
        return REDACTED_IMAGE_OCR_SOURCE_TYPE

    return IMAGE_OCR_SOURCE_TYPE


def ocr_confidence_label(text: str) -> str:
    """Return a coarse confidence label for OCR output."""
    normalized = normalize_ocr_text(text)

    if len(normalized) >= 250:
        return "Medium"

    if len(normalized) >= 40:
        return "Low"

    return "Very Low"


def build_image_ocr_result(page_number: int, text: str) -> ImageOcrResult | None:
    """Build an OCR result if useful visible text was extracted."""
    normalized_text = normalize_ocr_text(text)

    if not normalized_text:
        return None

    redaction_detected = contains_redaction_marker(normalized_text)

    return ImageOcrResult(
        page_number=page_number,
        text=normalized_text,
        source_type=classify_ocr_source_type(normalized_text),
        redaction_detected=redaction_detected,
        confidence=ocr_confidence_label(normalized_text),
    )


def render_pdf_page_to_image(page: fitz.Page, zoom: float = 2.0) -> Image.Image:
    """Render a PDF page to a PIL image for OCR."""
    matrix = fitz.Matrix(zoom, zoom)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    image_bytes = pixmap.tobytes("png")

    return Image.open(BytesIO(image_bytes))


def page_text_length(page: fitz.Page) -> int:
    """Return length of selectable PDF text on a page."""
    return len(normalize_ocr_text(page.get_text("text") or ""))


def extract_pdf_page_ocr(
    file_path: str | Path,
    *,
    min_text_chars: int = 100,
    force_ocr: bool = False,
    max_pages: int | None = None,
) -> list[ImageOcrResult]:
    """
    Extract OCR text from image-only or low-text PDF pages.

    By default, pages with enough selectable text are skipped. Use force_ocr=True
    for smoke tests or cases where visible figure labels should also be OCR'd.

    The returned text is visible OCR text only. Redacted content is not inferred.
    """
    path = Path(file_path)
    results: list[ImageOcrResult] = []

    with fitz.open(path) as document:
        page_count = len(document)

        if max_pages is not None:
            page_count = min(page_count, max_pages)

        for page_index in range(page_count):
            page = document[page_index]

            if not force_ocr and page_text_length(page) >= min_text_chars:
                continue

            image = render_pdf_page_to_image(page)
            ocr_text = pytesseract.image_to_string(image)

            result = build_image_ocr_result(
                page_number=page_index + 1,
                text=ocr_text,
            )

            if result is not None:
                results.append(result)

    return results


def image_ocr_results_to_chunks(
    results: Iterable[ImageOcrResult],
    *,
    file_name: str,
) -> list[dict[str, object]]:
    """
    Convert OCR results to lightweight chunk dictionaries.

    This keeps OCR evidence easy to wire into the existing ingestion/review flow.
    """
    chunks = []

    for index, result in enumerate(results):
        chunks.append(
            {
                "text": result.text,
                "metadata": {
                    "file_name": file_name,
                    "page_number": result.page_number,
                    "chunk_index": index,
                    "content_type": result.source_type,
                    "source_type": result.source_type,
                    "redaction_detected": result.redaction_detected,
                    "ocr_confidence": result.confidence,
                    "reviewer_note": (
                        "OCR detected redaction/confidentiality markers. "
                        "The backend cannot inspect or infer hidden content."
                        if result.redaction_detected
                        else (
                            "This evidence was extracted from image/OCR content "
                            "and should be verified against the source page."
                        )
                    ),
                },
            }
        )

    return chunks