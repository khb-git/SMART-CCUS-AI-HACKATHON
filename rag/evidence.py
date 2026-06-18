"""
Evidence packaging for retrieved chunks.

This module converts raw RetrievalResult objects into citation-ready evidence
blocks that can be passed into an answer-generation prompt.
"""

from __future__ import annotations

from dataclasses import dataclass

from rag.rag_types import Collection, RetrievalResult


DEFAULT_EXCERPT_CHARS = 800


@dataclass
class EvidenceItem:
    """A citation-ready evidence item for review answer generation."""

    evidence_id: str
    collection: Collection
    source_label: str
    source_document: str
    page_number: int
    chunk_index: int
    score: float
    content_type: str
    plan_type: str
    schema_section_id: str
    schema_section_title: str
    online_link: str
    source_page: str
    excerpt: str
    chunk_id: str = ""

    def to_dict(self):
        """Return JSON-serializable evidence metadata."""
        return {
            "evidence_id": self.evidence_id,
            "collection": self.collection.value,
            "source_label": self.source_label,
            "source_document": self.source_document,
            "page_number": self.page_number,
            "chunk_index": self.chunk_index,
            "score": self.score,
            "content_type": self.content_type,
            "plan_type": self.plan_type,
            "schema_section_id": self.schema_section_id,
            "schema_section_title": self.schema_section_title,
            "online_link": self.online_link,
            "source_page": self.source_page,
            "excerpt": self.excerpt,
            "chunk_id": self.chunk_id,
        }


def source_label_for_collection(collection: Collection) -> str:
    """Return a human-readable label for a vector collection."""
    collection = Collection(collection)

    if collection == Collection.REFERENCE:
        return "REGULATORY REFERENCE"

    if collection == Collection.PERMITS:
        return "PERMIT PRECEDENT"

    return collection.value.upper()


def make_excerpt(text: str, max_chars: int = DEFAULT_EXCERPT_CHARS) -> str:
    """Create a compact excerpt from chunk text."""
    cleaned = " ".join(str(text or "").split())

    if max_chars <= 0:
        return ""

    if len(cleaned) <= max_chars:
        return cleaned

    return cleaned[: max_chars - 3].rstrip() + "..."


def evidence_from_result(
    result: RetrievalResult,
    evidence_number: int,
    max_excerpt_chars: int = DEFAULT_EXCERPT_CHARS,
) -> EvidenceItem:
    """Convert one RetrievalResult into an EvidenceItem."""
    metadata = result.chunk.metadata
    collection = Collection(result.collection)

    return EvidenceItem(
        evidence_id=f"E{evidence_number}",
        collection=collection,
        source_label=source_label_for_collection(collection),
        source_document=metadata.source_document,
        page_number=metadata.page_number,
        chunk_index=metadata.chunk_index,
        score=result.score,
        content_type=metadata.content_type,
        plan_type=metadata.plan_type,
        schema_section_id=metadata.schema_section_id or metadata.section_id,
        schema_section_title=metadata.schema_section_title,
        online_link=metadata.online_link,
        source_page=metadata.source_page,
        excerpt=make_excerpt(result.chunk.text, max_chars=max_excerpt_chars),
        chunk_id=result.chunk.chunk_id,
    )


def package_evidence(
    results: list[RetrievalResult],
    start_index: int = 1,
    max_excerpt_chars: int = DEFAULT_EXCERPT_CHARS,
) -> list[EvidenceItem]:
    """Convert retrieval results into ordered evidence items."""
    evidence_items = []

    for offset, result in enumerate(results):
        evidence_items.append(
            evidence_from_result(
                result=result,
                evidence_number=start_index + offset,
                max_excerpt_chars=max_excerpt_chars,
            )
        )

    return evidence_items


def format_evidence_item(item: EvidenceItem) -> str:
    """Format one evidence item for prompt context."""
    section = ""

    if item.schema_section_id or item.schema_section_title:
        section = (
            f"Section: {item.schema_section_id} {item.schema_section_title}".strip()
        )

    lines = [
        f"[{item.evidence_id}] {item.source_label}",
        f"Source document: {item.source_document}",
        f"Page: {item.page_number}",
        f"Chunk index: {item.chunk_index}",
        f"Score: {item.score:.4f}",
        f"Content type: {item.content_type}",
    ]

    if item.plan_type:
        lines.append(f"Plan type: {item.plan_type}")

    if section:
        lines.append(section)

    if item.online_link:
        lines.append(f"Online link: {item.online_link}")

    if item.source_page:
        lines.append(f"Source page: {item.source_page}")

    lines.extend(
        [
            "Excerpt:",
            item.excerpt,
        ]
    )

    return "\n".join(lines)


def format_evidence_context(evidence_items: list[EvidenceItem]) -> str:
    """Format a list of evidence items for answer-generation prompts."""
    if not evidence_items:
        return "No evidence retrieved."

    return "\n\n".join(format_evidence_item(item) for item in evidence_items)