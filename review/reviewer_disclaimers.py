"""
Reviewer-facing disclaimers and known-limitations text.

These helpers centralize safety and scope language for review exports.
"""

from __future__ import annotations


CORE_REVIEW_DISCLAIMER = (
    "This report is a reviewer-support tool, not a final regulatory "
    "determination. Findings, evidence locations, checklist statuses, and "
    "recommended fixes should be confirmed by a qualified reviewer before final "
    "disposition."
)

OCR_REVIEW_DISCLAIMER = (
    "OCR-derived evidence is based on visible text only. The system does not "
    "inspect, recover, or infer hidden content behind redactions. OCR evidence "
    "should be verified against the source page."
)

EVIDENCE_STATUS_DISCLAIMER = (
    "`Evidence found` means related evidence was detected, but the checklist "
    "item may still be incomplete. `Present` means the deterministic checklist "
    "rules found enough evidence categories to credit the item, but reviewer "
    "confirmation is still required."
)

KNOWN_LIMITATIONS = [
    "The system uses deterministic rules and checklist terms; it may miss valid evidence written in unfamiliar language.",
    "The system may detect related evidence that does not fully satisfy a checklist requirement.",
    "OCR quality depends on source image quality, scan resolution, orientation, and page layout.",
    "Redacted or confidential pages are not interpreted beyond visible OCR text.",
    "Page numbers and evidence locations should be verified against the original source document.",
    "The system does not replace legal, engineering, or regulatory judgment.",
]


def build_reviewer_disclaimer_lines() -> list[str]:
    """Return Markdown lines for reviewer disclaimers."""
    return [
        "## Reviewer Disclaimers",
        "",
        CORE_REVIEW_DISCLAIMER,
        "",
        OCR_REVIEW_DISCLAIMER,
        "",
        EVIDENCE_STATUS_DISCLAIMER,
        "",
    ]


def build_known_limitations_lines() -> list[str]:
    """Return Markdown lines for known limitations."""
    lines = [
        "## Known Limitations",
        "",
    ]

    for limitation in KNOWN_LIMITATIONS:
        lines.append(f"- {limitation}")

    lines.append("")
    return lines