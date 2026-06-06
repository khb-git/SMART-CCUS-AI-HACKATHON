"""
Shared data types for the RAG pipeline.

Every module agrees on what a Chunk is and which collection it goes into.
If you change something here, you change the contract for everything else.
"""

from dataclasses import dataclass, field
from enum import Enum


class Collection(str, Enum):
    """The two vector store collections.

    PERMITS  — the seven Class VI permit applications (precedent).
               Answers "how have approved applicants handled X?"
    REFERENCE — 40 CFR Part 146 Subpart H and EPA guidance (rules).
               Answers "what does the regulation require for X?"

    These are kept strictly separate. Mixing them would let an applicant's
    interpretation be retrieved when the user asked for the rule.
    """

    PERMITS = "permits"
    REFERENCE = "reference"


class DocumentType(str, Enum):
    """What kind of source document a chunk came from."""

    PERMIT_APPLICATION = "permit_application"
    CFR_TEXT = "cfr_text"
    EPA_GUIDANCE = "epa_guidance"


@dataclass
class ChunkMetadata:
    """Metadata attached to every chunk in the vector store."""

    source_document: str
    document_type: DocumentType
    project_name: str = ""        # e.g. "adm_decatur" for permits, "" for reference
    section_id: str = ""          # e.g. "8" or "section_08"
    subsection_id: str = ""       # e.g. "7.2" for MAIP
    page_number: int = 0
    chunk_index: int = 0
    cfr_citation: str = ""        # e.g. "146.82(a)(1)" for reference chunks

    # Ingestion/review metadata added by the LangChain ingestion pipeline
    plan_type: str = ""
    schema_section_id: str = ""
    schema_section_title: str = ""
    content_type: str = "text"    # text or table
    table_index: int = -1
    sheet_name: str = ""
    row_start: int = -1
    row_end: int = -1
    local_path: str = ""
    online_link: str = ""
    source_page: str = ""
    summary: str = ""

    section_heading: str = ""
    local_section_title: str = ""
    detected_heading_on_page: str = ""

    def to_dict(self):
        """Flatten to a plain dict for vector store storage.

        Chroma metadata values must be primitive scalar values. Avoid None.
        """
        return {
            "source_document": self.source_document,
            "document_type": self.document_type.value,
            "project_name": self.project_name,
            "section_id": self.section_id,
            "subsection_id": self.subsection_id,
            "page_number": self.page_number,
            "chunk_index": self.chunk_index,
            "cfr_citation": self.cfr_citation,
            "plan_type": self.plan_type,
            "schema_section_id": self.schema_section_id,
            "schema_section_title": self.schema_section_title,
            "content_type": self.content_type,
            "table_index": self.table_index,
            "sheet_name": self.sheet_name,
            "row_start": self.row_start,
            "row_end": self.row_end,
            "local_path": self.local_path,
            "online_link": self.online_link,
            "source_page": self.source_page,
            "summary": self.summary,
            "section_heading": self.section_heading,
            "local_section_title": self.local_section_title,
            "detected_heading_on_page": self.detected_heading_on_page,
        }


@dataclass
class Chunk:
    """A piece of text ready to be embedded and stored."""

    text: str
    metadata: ChunkMetadata
    chunk_id: str = ""

    def __post_init__(self):
        if not self.text.strip():
            raise ValueError("Chunk text cannot be empty")


@dataclass
class RetrievalResult:
    """A chunk returned by retrieval, with its similarity score."""

    chunk: Chunk
    score: float
    collection: Collection
