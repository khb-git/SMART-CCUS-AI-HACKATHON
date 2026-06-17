"""
Schema-aware chunking for Class VI permit documents.

This is the most important file in the scaffold.

A blind character-based splitter would cut Section 7.2 (MAIP discussion)
mid-sentence and break the cross-reference logic the review engine needs.
Our chunker respects REVIEW_SCHEMA section boundaries: it detects section
headings, splits the document into section-bounded regions, and chunks
WITHIN regions — never across them. Every chunk carries its section_id
in metadata so the retriever can filter by section.
"""

import logging
import re

from rag.rag_types import Chunk, ChunkMetadata, DocumentType

logger = logging.getLogger(__name__)


# Default chunking parameters. Tuned for embedding model context windows
# (most sentence-transformers cap around 512 tokens / ~2000 chars).
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


# Matches section headings like:
#   "Section 7.2 Maximum Allowable Injection Pressure"
#   "7.2 MAIP"
#   "SECTION 7 - INJECTION OPERATIONS"
# Phase 2 will refine against real permit text.
SECTION_HEADING = re.compile(
    r"^(?:section\s+)?(\d{1,2})(?:\.(\d{1,2}))?\s+([A-Z][^\n]{3,100})$",
    re.IGNORECASE | re.MULTILINE,
)


def chunk_document(pages, source_path, document_type, project_name=""):
    """Chunk a loaded document into Chunk objects.

    Args:
        pages: list of (text, page_number) tuples from a loader.
        source_path: where the document came from (for metadata).
        document_type: DocumentType enum value.
        project_name: for permits only (e.g. "adm_decatur").

    Returns:
        list of Chunk objects ready to embed.

    TODO (Phase 2):
        1. Concatenate pages into one text stream, tracking offsets.
        2. Detect section boundaries with SECTION_HEADING.
        3. Validate boundaries against REVIEW_SCHEMA keys.
        4. Split into section regions; chunk within each region.
        5. Tag every chunk with section_id and subsection_id.
    """
    if not pages:
        return []

    logger.warning("chunk_document not yet implemented")
    return []


def detect_sections(text):
    """Find all section/subsection headings in text.

    Returns a list of (section_id, subsection_id, start_offset, heading_text).
    """
    # TODO: implement using SECTION_HEADING, cross-check against REVIEW_SCHEMA
    return []
