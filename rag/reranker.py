"""
Lightweight retrieval reranking.

This module reranks vector search results using lexical overlap between the
original user question and retrieved chunk text/metadata. It is intentionally
local, deterministic, and testable before introducing a learned reranker.
"""

from __future__ import annotations

import re
from dataclasses import replace

from rag.rag_types import RetrievalResult


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "does", "for",
    "from", "how", "in", "is", "it", "of", "on", "or", "the", "this", "to",
    "what", "when", "where", "which", "who", "why", "with",
}

TECHNICAL_TERMS = {
    "annulus",
    "annular",
    "casing",
    "continuous",
    "coriolis",
    "downhole",
    "flow",
    "flowmeter",
    "gauge",
    "injection",
    "meter",
    "monitor",
    "monitoring",
    "orifice",
    "pressure",
    "recording",
    "scada",
    "temperature",
    "transducer",
    "volume",
    "wellhead",
}


def tokenize(text: str) -> set[str]:
    """Tokenize text into useful lowercase terms."""
    tokens = re.findall(r"[a-zA-Z0-9]+", str(text or "").lower())
    return {
        token
        for token in tokens
        if len(token) > 2 and token not in STOPWORDS
    }


def result_text_for_reranking(result: RetrievalResult) -> str:
    """Combine chunk text and useful metadata for reranking."""
    metadata = result.chunk.metadata

    parts = [
        result.chunk.text,
        metadata.schema_section_title,
        metadata.section_heading,
        metadata.local_section_title,
        metadata.plan_type,
        metadata.content_type,
    ]

    return " ".join(str(part or "") for part in parts)


def lexical_relevance_score(question: str, result: RetrievalResult) -> float:
    """Compute a deterministic relevance score against the original question."""
    question_terms = tokenize(question)
    result_terms = tokenize(result_text_for_reranking(result))

    if not question_terms or not result_terms:
        return 0.0

    overlap = question_terms & result_terms
    technical_overlap = overlap & TECHNICAL_TERMS

    overlap_score = len(overlap) / max(len(question_terms), 1)
    technical_score = len(technical_overlap) * 0.05

    # Keep vector similarity as part of the final signal, but let exact
    # question/chunk term overlap move more direct answers upward.
    return result.score + overlap_score + technical_score


def rerank_results(question: str, results: list[RetrievalResult]) -> list[RetrievalResult]:
    """Return results sorted by combined vector + lexical relevance."""
    scored = []

    for result in results:
        rerank_score = lexical_relevance_score(question, result)
        scored.append((rerank_score, result))

    scored.sort(key=lambda item: item[0], reverse=True)

    reranked = []

    for rerank_score, result in scored:
        # Preserve the original retrieval score in the display-facing score for now.
        # Future work can add a separate rerank_score field to RetrievalResult.
        reranked.append(result)

    return reranked