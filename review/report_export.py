"""
Markdown report export for document review results.
"""

from __future__ import annotations

from typing import Any


def status_label(status: str) -> str:
    """Format status values for reports."""
    labels = {
        "review_ready": "Review ready",
        "mostly_complete": "Mostly complete",
        "incomplete": "Incomplete",
        "needs_revision": "Needs revision",
        "present": "Present",
        "partial": "Partial",
        "missing": "Missing",
        "unclear": "Unclear",
    }

    return labels.get(str(status or ""), str(status or "Unknown").replace("_", " ").title())


def finding_status_counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    """Count finding statuses."""
    counts = {
        "present": 0,
        "partial": 0,
        "missing": 0,
        "unclear": 0,
    }

    for finding in findings:
        status = finding.get("status", "")
        if status in counts:
            counts[status] += 1

    return counts


def finding_sort_key(finding: dict[str, Any]) -> tuple[int, str]:
    """Sort findings by review importance."""
    status_order = {
        "missing": 0,
        "partial": 1,
        "unclear": 2,
        "present": 3,
    }
    severity_order = {
        "critical": 0,
        "moderate": 1,
        "minor": 2,
    }

    return (
        status_order.get(finding.get("status", ""), 99),
        str(severity_order.get(finding.get("severity", ""), 99)),
    )


def format_list(values: list[str]) -> str:
    """Format a list for Markdown."""
    if not values:
        return "None found."

    return "\n".join(f"- {value}" for value in values)


def build_markdown_review_report(review_response: dict[str, Any]) -> str:
    """Build a Markdown report from /review-document response JSON."""
    report = review_response.get("report", {}) or {}
    classification = review_response.get("classification", {}) or {}
    findings = report.get("findings", []) or []
    counts = finding_status_counts(findings)

    document_name = review_response.get("document_name", "Unknown document")
    document_type = review_response.get("document_type", "unknown")
    classification_confidence = review_response.get(
        "classification_confidence",
        "unknown",
    )
    overall_status = report.get("overall_status", "unknown")
    summary = report.get("summary", "")
    storage_policy = review_response.get("storage_policy", "")

    lines = [
        "# Class VI Document Review Report",
        "",
        "## Document Summary",
        "",
        f"- **Document name:** {document_name}",
        f"- **Detected document type:** {document_type}",
        f"- **Classification confidence:** {classification_confidence}",
        f"- **Overall status:** {status_label(overall_status)}",
        f"- **Checklist ID:** {report.get('checklist_id', '')}",
        "",
        "## Review Summary",
        "",
        summary or "No summary returned.",
        "",
        "## Finding Counts",
        "",
        f"- **Present:** {counts['present']}",
        f"- **Partial:** {counts['partial']}",
        f"- **Missing:** {counts['missing']}",
        f"- **Unclear:** {counts['unclear']}",
        "",
        "## Classification Details",
        "",
        f"- **Classifier document type:** {classification.get('document_type', '')}",
        f"- **Confidence:** {classification.get('confidence', '')}",
        f"- **Matched terms:** {', '.join(classification.get('matched_terms', []) or []) or 'None'}",
        f"- **Reason:** {classification.get('reason', '')}",
        "",
    ]

    if storage_policy:
        lines.extend(
            [
                "## Storage Policy",
                "",
                storage_policy,
                "",
            ]
        )

    lines.extend(
        [
            "## Checklist Findings",
            "",
        ]
    )

    for finding in sorted(findings, key=finding_sort_key):
        status = finding.get("status", "")
        label = finding.get("label", finding.get("item_id", "Finding"))
        severity = finding.get("severity", "")
        requirement_level = finding.get("requirement_level", "")

        lines.extend(
            [
                f"### {status_label(status)} — {label}",
                "",
                f"- **Item ID:** {finding.get('item_id', '')}",
                f"- **Status:** {status_label(status)}",
                f"- **Requirement level:** {requirement_level}",
                f"- **Severity:** {severity}",
                "",
                "**Finding:**",
                "",
                finding.get("finding", "") or "No finding text returned.",
                "",
                "**Matched terms:**",
                "",
                format_list(finding.get("matched_terms", []) or []),
                "",
                "**Supporting excerpts:**",
                "",
                format_list(finding.get("supporting_excerpts", []) or []),
                "",
                "**Recommended fix:**",
                "",
                finding.get("recommended_fix", "") or "No recommended fix provided.",
                "",
            ]
        )

    return "\n".join(lines).strip() + "\n"


def default_report_filename(document_name: str) -> str:
    """Return a safe default Markdown report filename."""
    stem = str(document_name or "document").rsplit(".", 1)[0]
    safe = "".join(
        char if char.isalnum() or char in {"-", "_"} else "_"
        for char in stem
    ).strip("_")

    if not safe:
        safe = "document"

    return f"{safe}_review_report.md"