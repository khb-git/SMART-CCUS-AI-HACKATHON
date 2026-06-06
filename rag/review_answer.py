"""
Structured review answer generation.

This module builds reviewer-style answers from packaged evidence. It is
template-based for now so the answer structure is testable before we wire in
a local LLM.
"""

from __future__ import annotations

from dataclasses import dataclass

from rag.evidence import EvidenceItem, format_evidence_context


@dataclass
class ReviewAnswer:
    """Structured response for a Class VI review question."""

    question: str
    answer: str
    evidence_summary: str
    reviewer_interpretation: str
    potential_follow_up: str
    evidence_items: list[EvidenceItem]

    def to_dict(self):
        """Return JSON-serializable answer data."""
        return {
            "question": self.question,
            "answer": self.answer,
            "evidence_summary": self.evidence_summary,
            "reviewer_interpretation": self.reviewer_interpretation,
            "potential_follow_up": self.potential_follow_up,
            "evidence_items": [item.to_dict() for item in self.evidence_items],
        }


def split_evidence_by_collection(evidence_items: list[EvidenceItem]):
    """Split evidence into regulatory/reference and permit precedent groups."""
    reference = []
    permits = []

    for item in evidence_items:
        if item.collection.value == "reference":
            reference.append(item)
        elif item.collection.value == "permits":
            permits.append(item)

    return reference, permits


def summarize_evidence_sources(evidence_items: list[EvidenceItem]) -> str:
    """Create a compact source summary for the answer."""
    if not evidence_items:
        return "No evidence was retrieved."

    source_lines = []

    for item in evidence_items:
        source = item.source_document or "unknown source"
        page = f", p. {item.page_number}" if item.page_number else ""
        section = ""

        if item.schema_section_id or item.schema_section_title:
            section = f" — {item.schema_section_id} {item.schema_section_title}".strip()

        source_lines.append(
            f"[{item.evidence_id}] {item.source_label}: {source}{page}{section}"
        )

    return "\n".join(source_lines)


def build_template_answer(question: str, evidence_items: list[EvidenceItem]) -> ReviewAnswer:
    """Build a structured, reviewer-style answer from evidence.

    This does not invent facts beyond the retrieved evidence. It provides a
    stable answer scaffold that an LLM can later improve.
    """
    reference_items, permit_items = split_evidence_by_collection(evidence_items)

    if not evidence_items:
        answer = "Insufficient context to determine based on the retrieved evidence."
        evidence_summary = "No evidence was retrieved."
        reviewer_interpretation = (
            "The system did not retrieve enough supporting context to answer the "
            "review question."
        )
        potential_follow_up = (
            "Try broadening the query, removing metadata filters, or indexing more "
            "reference and permit documents."
        )

        return ReviewAnswer(
            question=question,
            answer=answer,
            evidence_summary=evidence_summary,
            reviewer_interpretation=reviewer_interpretation,
            potential_follow_up=potential_follow_up,
            evidence_items=[],
        )

    if reference_items and permit_items:
        answer = (
            "The retrieved evidence includes both regulatory/reference context and "
            "permit precedent. Use the reference evidence as the authoritative basis "
            "and the permit evidence as examples of how applicants have addressed the topic."
        )
    elif reference_items:
        answer = (
            "The retrieved evidence is regulatory/reference-focused. It can support "
            "an answer about EPA expectations, guidance, or Class VI requirements."
        )
    elif permit_items:
        answer = (
            "The retrieved evidence is permit-precedent-focused. It can support an "
            "answer about how applicants have addressed this topic in submitted plans."
        )
    else:
        answer = (
            "Evidence was retrieved, but it was not categorized as reference or permit "
            "precedent."
        )

    evidence_summary = summarize_evidence_sources(evidence_items)

    reviewer_interpretation = (
        "Review the evidence excerpts to determine whether the applicant's approach is "
        "consistent with Class VI expectations. Regulatory/reference evidence should be "
        "treated as controlling or guidance context, while permit-precedent evidence should "
        "be treated as examples rather than requirements."
    )

    potential_follow_up = (
        "If this is being used for a formal review, compare the retrieved permit evidence "
        "against the relevant EPA guidance or CFR citation and confirm whether the application "
        "contains all required supporting details."
    )

    return ReviewAnswer(
        question=question,
        answer=answer,
        evidence_summary=evidence_summary,
        reviewer_interpretation=reviewer_interpretation,
        potential_follow_up=potential_follow_up,
        evidence_items=evidence_items,
    )


def format_review_answer(review_answer: ReviewAnswer) -> str:
    """Format a ReviewAnswer for CLI or chatbot display."""
    evidence_context = format_evidence_context(review_answer.evidence_items)

    return f"""Question:
{review_answer.question}

Answer:
{review_answer.answer}

Evidence used:
{review_answer.evidence_summary}

Reviewer interpretation:
{review_answer.reviewer_interpretation}

Potential follow-up:
{review_answer.potential_follow_up}

Evidence excerpts:
{evidence_context}
"""