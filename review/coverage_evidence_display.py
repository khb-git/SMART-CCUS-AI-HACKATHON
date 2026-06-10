"""
Display helpers for package coverage evidence.
"""

from __future__ import annotations

from typing import Any


def coverage_evidence_rows_for_display(
    coverage_evidence: list[dict[str, Any]],
    max_terms: int = 8,
) -> list[dict[str, str]]:
    """Return package coverage evidence rows formatted for UI display."""
    rows: list[dict[str, str]] = []

    for evidence in sorted(
        coverage_evidence,
        key=lambda row: (
            row.get("plan_type", ""),
            row.get("document_name", ""),
            row.get("evidence_source", ""),
        ),
    ):
        matched_terms = evidence.get("matched_terms", []) or []
        matched_terms_text = ", ".join(matched_terms[:max_terms])

        if len(matched_terms) > max_terms:
            matched_terms_text += f", +{len(matched_terms) - max_terms} more"

        rows.append(
            {
                "Package topic": evidence.get("plan_type", "unknown"),
                "Document": evidence.get("document_name", "Unknown document"),
                "Primary type": evidence.get("document_type", "unknown"),
                "Evidence source": evidence.get("evidence_source", "coverage"),
                "Matched terms": matched_terms_text or "None",
                "Reviewer note": evidence.get("note", ""),
            }
        )

    return rows