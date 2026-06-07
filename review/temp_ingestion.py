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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ingestion.main import process_docx, process_pdf, process_xlsx


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


def copy_to_temporary_directory(source_path: str | Path, temp_dir: str | Path) -> Path:
    """Copy an uploaded file into a temporary directory for processing."""
    source_path = Path(source_path)
    temp_dir = Path(temp_dir)

    if not source_path.exists():
        raise FileNotFoundError(f"Uploaded file does not exist: {source_path}")

    destination = temp_dir / source_path.name
    shutil.copy2(source_path, destination)

    return destination


def process_temporary_file(
    file_path: str | Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
):
    """Process a temporary file into ingestion documents/chunks."""
    file_path = Path(file_path)
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        return process_pdf(
            file_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    if extension == ".docx":
        return process_docx(
            file_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    if extension == ".xlsx":
        return process_xlsx(file_path)

    raise ValueError(f"Unsupported review file type: {extension}")


def convert_ingestion_chunks(chunks) -> list[TemporaryReviewChunk]:
    """Convert ingestion document chunks into temporary review chunks."""
    review_chunks = []

    for chunk in chunks:
        text = getattr(chunk, "page_content", "") or ""
        metadata = dict(getattr(chunk, "metadata", {}) or {})

        review_chunks.append(
            TemporaryReviewChunk(
                text=text,
                metadata=metadata,
            )
        )

    return review_chunks


def ingest_review_document_temporarily(
    file_path: str | Path,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    keep_temporary_artifacts: bool = False,
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

        ingestion_chunks = process_temporary_file(
            copied_file,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        review_chunks = convert_ingestion_chunks(ingestion_chunks)

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

        ingestion_chunks = process_temporary_file(
            copied_file,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        review_chunks = convert_ingestion_chunks(ingestion_chunks)

        # Return extracted content only. Temporary paths are intentionally
        # cleared because the uploaded file has already been deleted.
        return TemporaryReviewDocument(
            original_filename=file_path.name,
            file_extension=file_path.suffix.lower(),
            chunks=review_chunks,
            temporary_directory="",
            temporary_file_path="",
        )