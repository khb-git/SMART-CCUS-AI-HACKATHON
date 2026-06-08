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
        "evidence_found": "Evidence found",
        "missing": "Missing",
        "unclear": "Unclear",
    }

    return labels.get(str(status or ""), str(status or "Unknown").replace("_", " ").title())


def finding_status_counts(findings: list[dict[str, Any]]) -> dict[str, int]:
    """Count finding statuses."""
    counts = {
        "present": 0,
        "evidence_found": 0,
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
        "evidence_found": 1,
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

def format_plan_type_list(values: list[str]) -> str:
    """Format plan type values for Markdown."""
    if not values:
        return "None."

    return "\n".join(f"- `{value}`" for value in values)

def format_document_names(values: list[str]) -> str:
    """Format document filenames for Markdown."""
    if not values:
        return "None."

    return "\n".join(f"- `{value}`" for value in values)


def build_markdown_findings_section(
    findings: list[dict[str, Any]],
    heading: str = "Priority findings",
) -> list[str]:
    """Build Markdown lines for priority findings."""
    lines: list[str] = []
    priority_findings = [
        finding
        for finding in sorted(findings, key=finding_sort_key)
        if finding.get("status") in {"missing", "evidence_found", "unclear"}
    ]

    if not priority_findings:
        return ["No priority findings.", ""]

    lines.extend([f"**{heading}:**", ""])

    for finding in priority_findings:
        lines.extend(
            [
                f"- **{status_label(finding.get('status', ''))}: "
                f"{finding.get('label', finding.get('item_id', 'Finding'))}**",
                f"  - {finding.get('finding', '')}",
            ]
        )

        matched_groups = finding.get("matched_evidence_group_names", []) or []
        if matched_groups:
            lines.append(
                "  - Matched evidence groups: "
                + ", ".join(f"`{group}`" for group in matched_groups)
            )

        recommended_fix = finding.get("recommended_fix", "")
        if recommended_fix:
            lines.append(f"  - Recommended fix: {recommended_fix}")

    lines.append("")
    return lines

def build_markdown_package_report(package_response: dict[str, Any]) -> str:
    """Build a Markdown report from /review-package response JSON."""
    report = package_response.get("report", {}) or {}

    package_name = package_response.get(
        "package_name",
        report.get("package_name", "uploaded_package"),
    )
    overall_status = report.get("overall_status", "unknown")
    summary = report.get("summary", "")
    storage_policy = package_response.get("storage_policy", "")

    detected_plan_types = report.get("detected_plan_types", []) or []
    missing_required_plan_types = (
        report.get("missing_required_plan_types", []) or []
    )
    missing_expected_plan_types = (
        report.get("missing_expected_plan_types", []) or []
    )
    duplicate_plan_types = report.get("duplicate_plan_types", []) or []
    unknown_documents = report.get("unknown_documents", []) or []
    supporting_documents = report.get("supporting_documents", []) or []
    expected_plan_types = report.get("expected_plan_types", []) or []
    required_plan_types = report.get("required_plan_types", []) or []
    document_reviews = report.get("document_reviews", []) or []

    lines = [
        "# Class VI Package Review Report",
        "",
        "## Package Summary",
        "",
        f"- **Package name:** {package_name}",
        f"- **Overall status:** {status_label(overall_status)}",
        f"- **Detected document types:** {len(detected_plan_types)}",
        f"- **Missing required document types:** {len(missing_required_plan_types)}",
        f"- **Missing expected document types:** {len(missing_expected_plan_types)}",
        f"- **Supporting documents:** {len(supporting_documents)}",
        f"- **Duplicate document types:** {len(duplicate_plan_types)}",
        f"- **Unknown documents:** {len(unknown_documents)}",
        "",
        "## Review Summary",
        "",
        summary or "No summary returned.",
        "",
        "## Detected Document Types",
        "",
        format_plan_type_list(detected_plan_types),
        "",
        "## Missing Required Document Types",
        "",
        format_plan_type_list(missing_required_plan_types),
        "",
        "## Missing Expected Document Types",
        "",
        format_plan_type_list(missing_expected_plan_types),
        "",
        "## Duplicate Document Types",
        "",
        format_plan_type_list(duplicate_plan_types),
        "",
        "## Unknown Documents",
        "",
        format_plan_type_list(unknown_documents),
        "",
        "## Supporting Documents",
        "",
        format_document_names(supporting_documents),
        "",
        "## Required Package Document Types",
        "",
        format_plan_type_list(required_plan_types),
        "",
        "## Expected Package Document Types",
        "",
        format_plan_type_list(expected_plan_types),
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
            "## Per-Document Review Summaries",
            "",
        ]
    )

    if not document_reviews:
        lines.extend(["No document reviews returned.", ""])
    else:
        for document_review in document_reviews:
            document_name = document_review.get("document_name", "Unknown document")
            document_type = document_review.get("document_type", "unknown")
            confidence = document_review.get(
                "classification_confidence",
                "unknown",
            )
            error = document_review.get("error", "")
            document_report = document_review.get("report") or {}
            classification = document_review.get("classification", {}) or {}
            document_role = document_review.get("document_role", "main")
            supporting_type = document_review.get("supporting_document_type", "")
            covered_plan_types = document_review.get("covered_plan_types", []) or []
            checklist_reports = document_review.get("checklist_reports", {}) or {}

            lines.extend(
                [
                    f"### {document_name}",
                    "",
                    f"- **Detected type:** `{document_type}`",
                    f"- **Classification confidence:** {confidence}",
                    f"- **Classifier matched terms:** "
                    f"{', '.join(classification.get('matched_terms', []) or []) or 'None'}",
                    f"- **Classifier reason:** {classification.get('reason', '')}",
                    "",
                    f"- **Document role:** {document_role}",
                    f"- **Supporting document type:** {supporting_type or 'N/A'}",
                    f"- **Covered plan types:** {', '.join(f'`{plan_type}`' for plan_type in covered_plan_types) or 'None'}",
                    f"- **Checklist reports:** {len(checklist_reports)}",
                ]
            )

            if checklist_reports:
                lines.extend(
                    [
                        "**Checklist reports by covered plan type:**",
                        "",
                    ]
                )

                for plan_type, checklist_report in checklist_reports.items():
                    findings = checklist_report.get("findings", []) or []
                    counts = finding_status_counts(findings)

                    lines.extend(
                        [
                            f"#### `{plan_type}`",
                            "",
                            f"- **Status:** {status_label(checklist_report.get('overall_status', 'unknown'))}",
                            f"- **Checklist ID:** {checklist_report.get('checklist_id', '')}",
                            f"- **Present:** {counts['present']}",
                            f"- **Evidence found:** {counts['evidence_found']}",
                            f"- **Missing:** {counts['missing']}",
                            f"- **Unclear:** {counts['unclear']}",
                            "",
                            checklist_report.get("summary", "") or "No summary returned.",
                            "",
                        ]
                    )

                    lines.extend(build_markdown_findings_section(findings))

                if not error:
                    continue

            if error:
                lines.extend(
                    [
                        "**Review error:**",
                        "",
                        error,
                        "",
                    ]
                )
                continue

            if not document_report:
                lines.extend(["No document report returned.", ""])
                continue

            findings = document_report.get("findings", []) or []
            counts = finding_status_counts(findings)

            lines.extend(
                [
                    f"- **Document review status:** "
                    f"{status_label(document_report.get('overall_status', 'unknown'))}",
                    f"- **Checklist ID:** {document_report.get('checklist_id', '')}",
                    "",
                    "**Document review summary:**",
                    "",
                    document_report.get("summary", "") or "No summary returned.",
                    "",
                    "**Finding counts:**",
                    "",
                    f"- Present: {counts['present']}",
                    f"- Evidence found: {counts['evidence_found']}",
                    f"- Missing: {counts['missing']}",
                    f"- Unclear: {counts['unclear']}",
                    "",
                ]
            )

            priority_findings = [
                finding
                for finding in sorted(findings, key=finding_sort_key)
                if finding.get("status") in {"missing", "evidence_found", "unclear"}
            ]

            if priority_findings:
                lines.extend(
                    [
                        "**Priority findings:**",
                        "",
                    ]
                )

                for finding in priority_findings:
                    lines.extend(
                        [
                            f"- **{status_label(finding.get('status', ''))}: "
                            f"{finding.get('label', finding.get('item_id', 'Finding'))}**",
                            f"  - {finding.get('finding', '')}",
                        ]
                    )

                    recommended_fix = finding.get("recommended_fix", "")
                    if recommended_fix:
                        lines.append(f"  - Recommended fix: {recommended_fix}")

                lines.append("")

    return "\n".join(lines).strip() + "\n"


def default_package_report_filename(package_name: str) -> str:
    """Return a safe default Markdown package report filename."""
    stem = str(package_name or "uploaded_package")
    safe = "".join(
        char if char.isalnum() or char in {"-", "_"} else "_"
        for char in stem
    ).strip("_")

    if not safe:
        safe = "uploaded_package"

    return f"{safe}_package_review_report.md"


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
        f"- **Evidence found:** {counts['evidence_found']}",
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