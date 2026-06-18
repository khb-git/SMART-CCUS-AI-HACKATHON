"""
Temporary document ingestion for uploaded review documents.

Uploaded user documents should not be stored permanently. This module processes
a file inside a temporary directory/session and returns extracted chunks for
review workflows without writing to permanent data/raw_docs, data/chunked, or
chroma_data.
"""

from __future__ import annotations

import shutil
import tempfile
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ingestion.main import process_docx, process_pdf, process_xlsx

from review.image_ocr import extract_pdf_page_ocr, image_ocr_results_to_chunks

SUPPORTED_REVIEW_EXTENSIONS = {".pdf", ".docx", ".xlsx"}


@dataclass
class TemporaryReviewChunk:
    """One temporary chunk extracted from an uploaded review document."""

    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TemporaryReviewDocument:
    """Temporary representation of an uploaded review document."""

    original_filename: str
    file_extension: str
    chunks: list[TemporaryReviewChunk]
    temporary_directory: str = ""
    temporary_file_path: str = ""

    def total_chunks(self) -> int:
        """Return number of extracted chunks."""
        return len(self.chunks)

    def combined_text(self) -> str:
        """Return all chunk text joined for simple review/classification."""
        return "\n\n".join(chunk.text for chunk in self.chunks if chunk.text)


def is_supported_review_file(path: str | Path) -> bool:
    """Return True if the uploaded file type is supported for temporary review."""
    return Path(path).suffix.lower() in SUPPORTED_REVIEW_EXTENSIONS

def is_table_chunk(metadata: dict[str, Any]) -> bool:
    """Return True when chunk metadata indicates table-like content."""
    content_type = str(metadata.get("content_type", "") or "").lower()
    return content_type == "table" or bool(metadata.get("table_index", -1) not in {-1, "", None})


def normalize_table_text(text: str) -> str:
    """Normalize table text into row-like lines for review matching."""
    lines = [
        " ".join(line.split())
        for line in str(text or "").splitlines()
        if line.strip()
    ]

    if not lines:
        return ""

    return "\n".join(f"Table row: {line}" for line in lines)


def enrich_temporary_chunk_text(text: str, metadata: dict[str, Any]) -> str:
    """Add lightweight context to table chunks without changing storage behavior."""
    if not is_table_chunk(metadata):
        return text

    normalized_table_text = normalize_table_text(text)

    if not normalized_table_text:
        return text

    table_label_parts = ["Table evidence"]

    page = metadata.get("page") or metadata.get("page_number")
    if page not in {"", None}:
        table_label_parts.append(f"page {page}")

    sheet_name = metadata.get("sheet_name")
    if sheet_name:
        table_label_parts.append(f"sheet {sheet_name}")

    table_index = metadata.get("table_index")
    if table_index not in {-1, "", None}:
        table_label_parts.append(f"table {table_index}")

    table_label = " | ".join(table_label_parts)

    return f"{table_label}\n{normalized_table_text}"

def build_ocr_review_chunks(
    file_path: str | Path,
    *,
    file_name: str,
    min_text_chars: int = 100,
    force_ocr: bool = False,
) -> list[TemporaryReviewChunk]:
    """Build temporary review chunks from OCR-visible PDF page text."""
    if Path(file_path).suffix.lower() != ".pdf":
        return []

    ocr_results = extract_pdf_page_ocr(
        file_path,
        min_text_chars=min_text_chars,
        force_ocr=force_ocr,
    )

    ocr_chunk_dicts = image_ocr_results_to_chunks(
        ocr_results,
        file_name=file_name,
    )

    return [
        TemporaryReviewChunk(
            text=str(chunk["text"]),
            metadata=dict(chunk["metadata"]),
        )
        for chunk in ocr_chunk_dicts
    ]

def copy_to_temporary_directory(source_path: str | Path, temp_dir: str | Path) -> Path:
    """Copy an uploaded file into a temporary directory for processing."""
    source_path = Path(source_path)
    temp_dir = Path(temp_dir)

    if not source_path.exists():
        raise FileNotFoundError(f"Uploaded file does not exist: {source_path}")

    destination = temp_dir / source_path.name
    shutil.copy2(source_path, destination)

    return destination


def load_chunks_from_temporary_output(output_root: str | Path):
    """Load chunk files written by ingestion processors from a temporary output root."""
    output_root = Path(output_root)
    chunks = []

    if not output_root.exists():
        return chunks

    for content_path in sorted(output_root.glob("*/*/content.txt")):
        chunk_dir = content_path.parent
        attr_path = chunk_dir / "attribute.json"

        text = content_path.read_text(encoding="utf-8")

        metadata = {}
        if attr_path.exists():
            metadata = json.loads(attr_path.read_text(encoding="utf-8"))

        if is_table_chunk(metadata):
            metadata["content_type"] = "table"
            metadata["table_aware"] = True

        chunks.append(
            TemporaryReviewChunk(
                text=enrich_temporary_chunk_text(text, metadata),
                metadata=metadata,
            )
        )

    return chunks

def process_temporary_file(
    file_path: str | Path,
    output_root: str | Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
):
    """Process a temporary file into temporary chunk files."""
    file_path = Path(file_path)
    output_root = Path(output_root)
    extension = file_path.suffix.lower()

    metadata = {
        "summary": "Temporary uploaded review document",
        "source_page": "",
        "url": "",
    }

    if extension == ".pdf":
        return process_pdf(
            file_path=file_path,
            output_root=output_root,
            metadata=metadata,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    if extension == ".docx":
        return process_docx(
            file_path=file_path,
            output_root=output_root,
            metadata=metadata,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    if extension == ".xlsx":
        return process_xlsx(
            file_path=file_path,
            output_root=output_root,
            metadata=metadata,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    raise ValueError(f"Unsupported review file type: {extension}")


def convert_ingestion_chunks(chunks) -> list[TemporaryReviewChunk]:
    """Convert ingestion document chunks into temporary review chunks."""
    review_chunks = []

    for chunk in chunks:
        text = getattr(chunk, "page_content", "") or ""
        metadata = dict(getattr(chunk, "metadata", {}) or {})

        if is_table_chunk(metadata):
            metadata["content_type"] = "table"
            metadata["table_aware"] = True

        review_chunks.append(
            TemporaryReviewChunk(
                text=enrich_temporary_chunk_text(text, metadata),
                metadata=metadata,
            )
        )

    return review_chunks


def ingest_review_document_temporarily(
    file_path: str | Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    keep_temporary_artifacts: bool = False,
    enable_ocr: bool = True,
    force_ocr: bool = False,
    ocr_min_text_chars: int = 100,
) -> TemporaryReviewDocument:
    """Temporarily ingest an uploaded review document.

    By default, all temporary files are deleted before this function returns.
    Set keep_temporary_artifacts=True only for debugging/tests.
    """
    file_path = Path(file_path)

    if not is_supported_review_file(file_path):
        raise ValueError(f"Unsupported review file type: {file_path.suffix}")

    if keep_temporary_artifacts:
        temp_dir = Path(tempfile.mkdtemp())
        copied_file = copy_to_temporary_directory(file_path, temp_dir)

        output_root = temp_dir / "chunked"

        process_temporary_file(
            copied_file,
            output_root=output_root,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        review_chunks = load_chunks_from_temporary_output(output_root)

        if enable_ocr:
            review_chunks.extend(
                build_ocr_review_chunks(
                    copied_file,
                    file_name=file_path.name,
                    min_text_chars=ocr_min_text_chars,
                    force_ocr=force_ocr,
                )
            )

        return TemporaryReviewDocument(
            original_filename=file_path.name,
            file_extension=file_path.suffix.lower(),
            chunks=review_chunks,
            temporary_directory=str(temp_dir),
            temporary_file_path=str(copied_file),
        )

    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        copied_file = copy_to_temporary_directory(file_path, temp_dir)

        output_root = temp_dir / "chunked"

        process_temporary_file(
            copied_file,
            output_root=output_root,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        review_chunks = load_chunks_from_temporary_output(output_root)

        if enable_ocr:
            review_chunks.extend(
                build_ocr_review_chunks(
                    copied_file,
                    file_name=file_path.name,
                    min_text_chars=ocr_min_text_chars,
                    force_ocr=force_ocr,
                )
            )

        # Return extracted content only. Temporary paths are intentionally
        # cleared because the uploaded file has already been deleted.
        return TemporaryReviewDocument(
            original_filename=file_path.name,
            file_extension=file_path.suffix.lower(),
            chunks=review_chunks,
            temporary_directory="",
            temporary_file_path="",
        )