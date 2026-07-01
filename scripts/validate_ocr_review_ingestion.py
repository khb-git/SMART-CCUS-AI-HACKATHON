"""
Validate OCR behavior for a local review document.

This script is intended for manual validation with real PDFs that should not be
committed to the repository. It temporarily ingests the document and reports
OCR-derived chunks, source labels, page numbers, redaction flags, and reviewer
notes.

Example:
    python scripts/validate_ocr_review_ingestion.py "C:\\path\\to\\redacted.pdf" --force-ocr
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from review.temp_ingestion import TemporaryReviewChunk, ingest_review_document_temporarily


OCR_SOURCE_TYPES = {"image_ocr", "redacted_image_ocr"}


def chunk_source_type(chunk: TemporaryReviewChunk) -> str:
    """Return normalized evidence source type for a temporary review chunk."""
    return str(
        chunk.metadata.get("source_type")
        or chunk.metadata.get("content_type")
        or "text"
    )


def is_ocr_chunk(chunk: TemporaryReviewChunk) -> bool:
    """Return whether a chunk came from OCR-derived evidence."""
    return chunk_source_type(chunk) in OCR_SOURCE_TYPES


def shorten_text(value: str, max_chars: int = 240) -> str:
    """Return a compact single-line excerpt."""
    text = " ".join(str(value or "").split())

    if len(text) <= max_chars:
        return text

    return text[:max_chars].rsplit(" ", 1)[0].strip() + "..."


def summarize_ocr_chunk(chunk: TemporaryReviewChunk) -> dict[str, Any]:
    """Return reviewer-facing summary data for one OCR chunk."""
    metadata = chunk.metadata

    return {
        "page_number": metadata.get("page_number") or metadata.get("page"),
        "source_type": chunk_source_type(chunk),
        "redaction_detected": bool(metadata.get("redaction_detected")),
        "ocr_confidence": metadata.get("ocr_confidence", "Unknown"),
        "reviewer_note": metadata.get("reviewer_note", ""),
        "excerpt": shorten_text(chunk.text),
    }


def summarize_ocr_chunks(chunks: list[TemporaryReviewChunk]) -> list[dict[str, Any]]:
    """Return OCR summaries from temporary review chunks."""
    return [summarize_ocr_chunk(chunk) for chunk in chunks if is_ocr_chunk(chunk)]


def print_ocr_summary(
    *,
    file_path: Path,
    total_chunks: int,
    ocr_summaries: list[dict[str, Any]],
) -> None:
    """Print a readable OCR validation summary."""
    redacted_count = sum(
        1
        for summary in ocr_summaries
        if summary["source_type"] == "redacted_image_ocr"
        or summary["redaction_detected"]
    )

    print("")
    print("OCR validation summary")
    print("======================")
    print(f"File: {file_path}")
    print(f"Total chunks: {total_chunks}")
    print(f"OCR chunks: {len(ocr_summaries)}")
    print(f"Redacted OCR chunks: {redacted_count}")
    print("")

    if not ocr_summaries:
        print("No OCR-derived chunks were returned.")
        return

    for index, summary in enumerate(ocr_summaries, start=1):
        print(f"OCR chunk {index}")
        print("-" * 40)
        print(f"Page: {summary['page_number'] or 'Not found'}")
        print(f"Source type: {summary['source_type']}")
        print(f"Redaction detected: {summary['redaction_detected']}")
        print(f"OCR confidence: {summary['ocr_confidence']}")
        print(f"Reviewer note: {summary['reviewer_note'] or 'None'}")
        print(f"Excerpt: {summary['excerpt'] or 'None'}")
        print("")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Validate image OCR behavior for a local review document."
    )

    parser.add_argument(
        "file_path",
        help="Path to a local PDF review document.",
    )
    parser.add_argument(
        "--force-ocr",
        action="store_true",
        help="Run OCR even when a page already has selectable text.",
    )
    parser.add_argument(
        "--ocr-min-text-chars",
        type=int,
        default=100,
        help="Selectable-text threshold below which PDF pages are OCR'd.",
    )
    parser.add_argument(
        "--disable-ocr",
        action="store_true",
        help="Disable OCR and show that no OCR chunks are appended.",
    )

    return parser.parse_args()


def main() -> None:
    """Run OCR validation for a local review document."""
    args = parse_args()
    file_path = Path(args.file_path)

    document = ingest_review_document_temporarily(
        file_path,
        enable_ocr=not args.disable_ocr,
        force_ocr=args.force_ocr,
        ocr_min_text_chars=args.ocr_min_text_chars,
    )

    ocr_summaries = summarize_ocr_chunks(document.chunks)

    print_ocr_summary(
        file_path=file_path,
        total_chunks=document.total_chunks(),
        ocr_summaries=ocr_summaries,
    )


if __name__ == "__main__":
    main()