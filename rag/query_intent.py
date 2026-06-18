"""
Rule-based query intent routing for the Class VI review assistant.

This module decides whether a question should retrieve:
- regulatory/reference evidence
- permit precedent evidence
- both
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from rag.rag_types import Collection


class QueryIntent(str, Enum):
    """Supported retrieval intents."""

    REGULATORY_REQUIREMENT = "regulatory_requirement"
    PERMIT_PRECEDENT = "permit_precedent"
    CROSS_CHECK = "cross_check"
    GENERAL_REVIEW = "general_review"


@dataclass
class QueryRoute:
    """Routing decision for a user question."""

    intent: QueryIntent
    collections: list[Collection]
    reason: str

    def uses_reference(self) -> bool:
        return Collection.REFERENCE in self.collections

    def uses_permits(self) -> bool:
        return Collection.PERMITS in self.collections


REFERENCE_TERMS = [
    "require",
    "requires",
    "required",
    "requirement",
    "requirements",
    "regulation",
    "regulations",
    "regulatory",
    "rule",
    "rules",
    "cfr",
    "40 cfr",
    "epa require",
    "epa expects",
    "guidance",
    "what does epa",
    "what does class vi require",
    "must include",
    "shall",
]

PERMIT_PRECEDENT_TERMS = [
    "applicant",
    "applicants",
    "approved applicants",
    "how do applicants",
    "how have applicants",
    "permit precedent",
    "precedent",
    "examples",
    "example",
    "submitted plans",
    "permit applications",
    "how did",
    "how does adm",
    "how does one earth",
    "how does hgcs",
    "how does wabash",
    "how does marquis",
    "how does lorain",
]

CROSS_CHECK_TERMS = [
    "compare",
    "cross check",
    "cross-check",
    "against",
    "consistent with",
    "match",
    "matches",
    "does the application",
    "does this application",
    "is the application",
    "is this consistent",
    "gap",
    "gaps",
    "deficiency",
    "deficiencies",
    "missing",
    "sufficient",
    "adequate",
    "review",
    "evaluate",
]


def normalize_query(query: str) -> str:
    """Normalize user question for lightweight intent matching."""
    return (
        str(query or "")
        .lower()
        .replace("-", " ")
        .replace("_", " ")
        .replace("?", " ")
        .strip()
    )


def count_matches(text: str, terms: list[str]) -> int:
    """Count simple keyword/phrase matches."""
    return sum(1 for term in terms if term in text)


def classify_query_intent(query: str) -> QueryRoute:
    """Classify a query into a retrieval route.

    This is intentionally rule-based for now. It gives predictable behavior
    before any LLM-based router is introduced.
    """
    normalized = normalize_query(query)

    reference_hits = count_matches(normalized, REFERENCE_TERMS)
    permit_hits = count_matches(normalized, PERMIT_PRECEDENT_TERMS)
    cross_hits = count_matches(normalized, CROSS_CHECK_TERMS)

    if cross_hits and (reference_hits or permit_hits):
        return QueryRoute(
            intent=QueryIntent.CROSS_CHECK,
            collections=[Collection.REFERENCE, Collection.PERMITS],
            reason="Query asks for comparison, review, sufficiency, or consistency.",
        )

    if cross_hits and not (reference_hits or permit_hits):
        return QueryRoute(
            intent=QueryIntent.CROSS_CHECK,
            collections=[Collection.REFERENCE, Collection.PERMITS],
            reason="Query appears to ask for review or gap analysis.",
        )

    if reference_hits > permit_hits:
        return QueryRoute(
            intent=QueryIntent.REGULATORY_REQUIREMENT,
            collections=[Collection.REFERENCE],
            reason="Query asks about requirements, regulations, EPA expectations, or CFR.",
        )

    if permit_hits > reference_hits:
        return QueryRoute(
            intent=QueryIntent.PERMIT_PRECEDENT,
            collections=[Collection.PERMITS],
            reason="Query asks how applicants or permit examples handled the topic.",
        )

    return QueryRoute(
        intent=QueryIntent.GENERAL_REVIEW,
        collections=[Collection.REFERENCE, Collection.PERMITS],
        reason="No specific intent dominated, so both reference and permit evidence are useful.",
    )