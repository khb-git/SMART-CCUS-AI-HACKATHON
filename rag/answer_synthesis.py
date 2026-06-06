"""
Evidence-grounded answer synthesis.

This module builds a more specific answer from retrieved evidence excerpts
without calling an LLM. It is intentionally extractive: it selects relevant
sentences from evidence instead of inventing new claims.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from rag.evidence import EvidenceItem
from rag.types import Collection


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "does", "for",
    "from", "how", "in", "is", "it", "of", "on", "or", "the", "this", "to",
    "what", "when", "where", "which", "who", "why", "with",
}

TECHNICAL_BOOST_TERMS = {
    "annulus",
    "casing",
    "co2",
    "continuous",
    "flow",
    "flowmeter",
    "formation",
    "frequency",
    "groundwater",
    "injection",
    "monitor",
    "monitoring",
    "pressure",
    "recording",
    "sample",
    "sampling",
    "temperature",
    "testing",
    "volume",
    "well",
    "wellhead",
}


@dataclass
class EvidenceSentence:
    """A scored sentence extracted from an evidence item."""

    evidence_id: str
    collection: Collection
    sentence: str
    score: float


def tokenize(text: str) -> set[str]:
    """Tokenize text into meaningful lowercase words."""
    tokens = re.findall(r"[a-zA-Z0-9]+", str(text or "").lower())
    return {token for token in tokens if token not in STOPWORDS and len(token) > 2}


def split_sentences(text: str) -> list[str]:
    """Split text into sentence-like units.

    This is deliberately lightweight and handles imperfect PDF extraction.
    """
    cleaned = " ".join(str(text or "").split())
    if not cleaned:
        return []

    pieces = re.split(r"(?<=[.!?])\s+", cleaned)
    sentences = []

    for piece in pieces:
        piece = piece.strip()
        if len(piece) < 20:
            continue
        sentences.append(piece)

    return sentences


def score_sentence(question_terms: set[str], sentence: str) -> float:
    """Score a sentence against the question and technical vocabulary."""
    sentence_terms = tokenize(sentence)

    if not sentence_terms:
        return 0.0

    overlap = len(question_terms & sentence_terms)
    technical_hits = len(sentence_terms & TECHNICAL_BOOST_TERMS)

    return float(overlap * 2 + technical_hits)


def extract_relevant_sentences(
    question: str,
    evidence_items: list[EvidenceItem],
    max_sentences: int = 5,
) -> list[EvidenceSentence]:
    """Extract the most relevant evidence sentences for a question.

    Strategy:
    - Score all sentences by overlap with query terms and technical terms.
    - Prefer one strong sentence from each evidence item first.
    - Fill remaining slots by global score.
    """
    if max_sentences <= 0:
        return []

    question_terms = tokenize(question)
    all_candidates: list[EvidenceSentence] = []

    for item in evidence_items:
        sentences = split_sentences(item.excerpt)

        for sentence in sentences:
            score = score_sentence(question_terms, sentence)

            if score <= 0:
                continue

            all_candidates.append(
                EvidenceSentence(
                    evidence_id=item.evidence_id,
                    collection=item.collection,
                    sentence=sentence,
                    score=score,
                )
            )

    all_candidates.sort(key=lambda candidate: candidate.score, reverse=True)

    selected: list[EvidenceSentence] = []
    used_evidence_ids = set()

    # First pass: one best sentence per evidence item.
    for candidate in all_candidates:
        if candidate.evidence_id in used_evidence_ids:
            continue

        selected.append(candidate)
        used_evidence_ids.add(candidate.evidence_id)

        if len(selected) >= max_sentences:
            return selected

    # Second pass: allow additional strong sentences if slots remain.
    selected_sentences = {candidate.sentence for candidate in selected}

    for candidate in all_candidates:
        if candidate.sentence in selected_sentences:
            continue

        selected.append(candidate)
        selected_sentences.add(candidate.sentence)

        if len(selected) >= max_sentences:
            break

    return selected


def collection_phrase(evidence_items: list[EvidenceItem]) -> str:
    """Describe what evidence types were used."""
    has_reference = any(item.collection == Collection.REFERENCE for item in evidence_items)
    has_permits = any(item.collection == Collection.PERMITS for item in evidence_items)

    if has_reference and has_permits:
        return "the retrieved regulatory/reference and permit-precedent evidence"

    if has_reference:
        return "the retrieved regulatory/reference evidence"

    if has_permits:
        return "the retrieved permit-precedent evidence"

    return "the retrieved evidence"


def build_evidence_grounded_answer(
    question: str,
    evidence_items: list[EvidenceItem],
    max_sentences: int = 5,
) -> str:
    """Build a concise answer grounded in retrieved evidence excerpts."""
    if not evidence_items:
        return "Insufficient context to determine based on the retrieved evidence."

    relevant_sentences = extract_relevant_sentences(
        question=question,
        evidence_items=evidence_items,
        max_sentences=max_sentences,
    )

    if not relevant_sentences:
        return (
            "The system retrieved evidence, but the excerpts did not contain enough "
            "directly relevant text to synthesize a specific answer."
        )

    lines = [
        f"Based on {collection_phrase(evidence_items)}, the following points are supported:"
    ]

    for item in relevant_sentences:
        lines.append(f"- [{item.evidence_id}] {item.sentence}")

    return "\n".join(lines)