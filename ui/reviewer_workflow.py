"""Reviewer workflow helpers for the Streamlit package review UI."""

from __future__ import annotations

import csv
import json
from io import StringIO
from typing import Mapping

from review.report_export import markdown_table_escape


REVIEWER_CONFIRMATION_OPTIONS = [
    "Pending review",
    "Confirmed",
    "Needs follow-up",
    "Not applicable",
    "Resolved after cross-reference",
]


def reviewer_safe_key(value: str) -> str:
    """Return a Streamlit-safe key fragment."""
    return "".join(
        char if char.isalnum() else "_"
        for char in value
    )


def reviewer_confirmation_state_key(row: dict[str, str]) -> str:
    """Return stable Streamlit state key for one reviewer confirmation row."""
    review_key = row.get("Review Key", "")
    return f"reviewer_confirmation_{reviewer_safe_key(review_key)}"


def reviewer_note_state_key(row: dict[str, str]) -> str:
    """Return stable Streamlit state key for one reviewer note row."""
    review_key = row.get("Review Key", "")
    return f"reviewer_note_{reviewer_safe_key(review_key)}"


def apply_reviewer_confirmations(
    rows: list[dict[str, str]],
    session_state: Mapping[str, str] | None = None,
) -> list[dict[str, str]]:
    """Attach reviewer confirmation and note state to checklist display rows."""
    state = session_state or {}
    confirmed_rows = []

    for row in rows:
        confirmation_key = reviewer_confirmation_state_key(row)
        note_key = reviewer_note_state_key(row)

        confirmation = state.get(confirmation_key, "Pending review")
        reviewer_note = state.get(note_key, "")

        confirmed_row = dict(row)
        confirmed_row["Reviewer Confirmation"] = confirmation
        confirmed_row["Reviewer Notes"] = reviewer_note
        confirmed_rows.append(confirmed_row)

    return confirmed_rows


def reviewer_confirmation_counts(
    rows: list[dict[str, str]],
) -> dict[str, int]:
    """Count reviewer confirmation values for displayed checklist rows."""
    counts = {
        option: 0
        for option in REVIEWER_CONFIRMATION_OPTIONS
    }

    for row in rows:
        confirmation = row.get("Reviewer Confirmation", "Pending review")

        if confirmation not in counts:
            confirmation = "Pending review"

        counts[confirmation] += 1

    return counts

def build_reviewer_confirmation_summary_section(
    rows: list[dict[str, str]],
) -> str:
    """Build Markdown summary counts for reviewer confirmations."""
    counts = reviewer_confirmation_counts(rows)

    lines = [
        "## Reviewer Confirmation Summary",
        "",
        "| Reviewer Confirmation | Count |",
        "| --- | ---: |",
    ]

    for option in REVIEWER_CONFIRMATION_OPTIONS:
        lines.append(f"| {markdown_table_escape(option)} | {counts[option]} |")

    lines.append("")
    return "\n".join(lines)

def filter_rows_by_reviewer_confirmation(
    rows: list[dict[str, str]],
    selected_confirmations: list[str],
) -> list[dict[str, str]]:
    """Return rows matching selected reviewer confirmation values."""
    if not selected_confirmations:
        return rows

    return [
        row
        for row in rows
        if row.get("Reviewer Confirmation", "Pending review")
        in selected_confirmations
    ]


def build_reviewer_confirmation_export_section(
    rows: list[dict[str, str]],
) -> str:
    """Build Markdown section for reviewer confirmation states."""
    lines = [
        "## Reviewer Confirmation Export",
        "",
        (
            "This section reflects reviewer confirmation selections from the "
            "current Streamlit session. These values are not persisted unless "
            "the exported report is saved."
        ),
        "",
    ]

    if not rows:
        return "\n".join(lines + ["No reviewer confirmation rows were available.", ""])

    lines.extend(
        [
            "| Reviewer Confirmation | Reviewer Notes | Status | Required Item | GSDT Module/Folder | File Name | Page Number |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_table_escape(row.get("Reviewer Confirmation", "Pending review")),
                    markdown_table_escape(row.get("Reviewer Notes", "")),
                    markdown_table_escape(row.get("Status", "")),
                    markdown_table_escape(row.get("Required Item", "")),
                    markdown_table_escape(row.get("GSDT Module/Folder", "")),
                    markdown_table_escape(row.get("File Name", "")),
                    markdown_table_escape(row.get("Page Number", "")),
                ]
            )
            + " |"
        )

    lines.append("")
    return "\n".join(lines)

def is_maip_reviewer_row(row: dict[str, str]) -> bool:
    """Return whether a reviewer row belongs to MAIP validation."""
    review_key = row.get("Review Key", "")
    module_folder = row.get("GSDT Module/Folder", "")

    return (
        review_key.startswith("MAIP::")
        or module_folder == "MAIP Cross-Reference Validation"
    )


def split_maip_reviewer_rows(
    rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Split reviewer rows into checklist rows and MAIP rows."""
    checklist_rows = []
    maip_rows = []

    for row in rows:
        if is_maip_reviewer_row(row):
            maip_rows.append(row)
        else:
            checklist_rows.append(row)

    return checklist_rows, maip_rows


def build_maip_reviewer_confirmation_export_section(
    rows: list[dict[str, str]],
) -> str:
    """Build Markdown section for MAIP reviewer confirmation states."""
    _checklist_rows, maip_rows = split_maip_reviewer_rows(rows)

    lines = [
        "## MAIP Reviewer Confirmation Export",
        "",
        (
            "This section reflects reviewer confirmation selections for MAIP "
            "cross-reference findings from the current Streamlit session. "
            "These values should be used as reviewer annotations, not as a "
            "replacement for the deterministic MAIP validation results."
        ),
        "",
    ]

    if not maip_rows:
        return "\n".join(lines + ["No MAIP reviewer confirmation rows were available.", ""])

    lines.extend(
        [
            "| Reviewer Confirmation | Reviewer Notes | Status | Severity | Finding | Message | Recommended Action | Supporting Values |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for row in maip_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_table_escape(row.get("Reviewer Confirmation", "Pending review")),
                    markdown_table_escape(row.get("Reviewer Notes", "")),
                    markdown_table_escape(row.get("Status", "")),
                    markdown_table_escape(row.get("Severity", "")),
                    markdown_table_escape(row.get("Finding", "")),
                    markdown_table_escape(row.get("Message", "")),
                    markdown_table_escape(row.get("Recommended Action", "")),
                    markdown_table_escape(row.get("Supporting Values", "")),
                ]
            )
            + " |"
        )

    lines.append("")
    return "\n".join(lines)


def append_maip_reviewer_confirmation_export(
    markdown_report: str,
    rows: list[dict[str, str]],
) -> str:
    """Append MAIP reviewer confirmation export rows to a Markdown report."""
    section = build_maip_reviewer_confirmation_export_section(rows)
    return markdown_report.rstrip() + "\n\n" + section.rstrip() + "\n"

MAIP_DEFICIENCY_STATUS_LABELS = [
    "Missing Evidence",
    "Warning",
    "Fail",
]


def filter_maip_deficiency_rows(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Return MAIP reviewer rows that need reviewer follow-up."""
    _checklist_rows, maip_rows = split_maip_reviewer_rows(rows)

    return [
        row
        for row in maip_rows
        if any(
            status_label in row.get("Status", "")
            for status_label in MAIP_DEFICIENCY_STATUS_LABELS
        )
    ]


def build_maip_deficiency_csv(
    rows: list[dict[str, str]],
) -> str:
    """Build CSV text for unresolved MAIP validation rows only."""
    output = StringIO()

    fieldnames = [
        "Reviewer Confirmation",
        "Reviewer Notes",
        "Status",
        "Severity",
        "Finding",
        "Message",
        "Recommended Action",
        "Supporting Values",
    ]

    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        extrasaction="ignore",
    )
    writer.writeheader()

    for row in filter_maip_deficiency_rows(rows):
        writer.writerow(
            {
                "Reviewer Confirmation": row.get(
                    "Reviewer Confirmation",
                    "Pending review",
                ),
                "Reviewer Notes": row.get("Reviewer Notes", ""),
                "Status": row.get("Status", ""),
                "Severity": row.get("Severity", ""),
                "Finding": row.get("Finding", ""),
                "Message": row.get("Message", ""),
                "Recommended Action": row.get("Recommended Action", ""),
                "Supporting Values": row.get("Supporting Values", ""),
            }
        )

    return output.getvalue()

def append_reviewer_confirmation_export(
    markdown_report: str,
    rows: list[dict[str, str]],
) -> str:
    """Append reviewer confirmation export rows to a Markdown package report."""
    section = build_reviewer_confirmation_export_section(rows)
    return markdown_report.rstrip() + "\n\n" + section.rstrip() + "\n"

def build_reviewer_state_export(
    rows: list[dict[str, str]],
    package_name: str = "",
) -> str:
    """Build portable JSON text for reviewer confirmations and notes."""
    reviewer_state_rows = []

    for row in rows:
        review_key = row.get("Review Key", "")

        if not review_key:
            continue

        reviewer_state_rows.append(
            {
                "Review Key": review_key,
                "Reviewer Confirmation": row.get(
                    "Reviewer Confirmation",
                    "Pending review",
                ),
                "Reviewer Notes": row.get("Reviewer Notes", ""),
                "Status": row.get("Status", ""),
                "Required Item": row.get("Required Item", ""),
                "GSDT Module/Folder": row.get("GSDT Module/Folder", ""),
                "Regulatory Citation": row.get("Regulatory Citation", ""),
                "File Name": row.get("File Name", ""),
                "Page Number": row.get("Page Number", ""),
            }
        )

    return json.dumps(
        {
            "version": 1,
            "package_name": package_name,
            "reviewer_state": reviewer_state_rows,
        },
        indent=2,
    )


def parse_reviewer_state_import(json_text: str) -> dict[str, str]:
    """Parse reviewer state JSON into Streamlit session-state key values."""
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError("Reviewer state file is not valid JSON.") from exc

    if not isinstance(payload, dict):
        raise ValueError("Reviewer state file must contain a JSON object.")

    reviewer_state_rows = payload.get("reviewer_state", [])

    if not isinstance(reviewer_state_rows, list):
        raise ValueError("Reviewer state file must contain a reviewer_state list.")

    session_updates: dict[str, str] = {}

    for row in reviewer_state_rows:
        if not isinstance(row, dict):
            continue

        review_key = str(row.get("Review Key", ""))

        if not review_key:
            continue

        confirmation = str(
            row.get("Reviewer Confirmation", "Pending review")
        )

        if confirmation not in REVIEWER_CONFIRMATION_OPTIONS:
            confirmation = "Pending review"

        reviewer_note = str(row.get("Reviewer Notes", ""))

        key_row = {"Review Key": review_key}

        session_updates[reviewer_confirmation_state_key(key_row)] = confirmation
        session_updates[reviewer_note_state_key(key_row)] = reviewer_note

    return session_updates

def build_completeness_checklist_csv(
    rows: list[dict[str, str]],
) -> str:
    """Build CSV text for completeness checklist rows."""
    output = StringIO()

    fieldnames = [
        "Reviewer Confirmation",
        "Reviewer Notes",
        "Status",
        "Required Item",
        "GSDT Module/Folder",
        "Regulatory Citation",
        "File Name",
        "Page Number",
        "Notes",
    ]

    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        extrasaction="ignore",
    )
    writer.writeheader()

    for row in rows:
        writer.writerow(
            {
                "Reviewer Confirmation": row.get(
                    "Reviewer Confirmation",
                    "Pending review",
                ),
                "Reviewer Notes": row.get("Reviewer Notes", ""),
                "Status": row.get("Status", ""),
                "Required Item": row.get("Required Item", ""),
                "GSDT Module/Folder": row.get("GSDT Module/Folder", ""),
                "Regulatory Citation": row.get("Regulatory Citation", ""),
                "File Name": row.get("File Name", ""),
                "Page Number": row.get("Page Number", ""),
                "Notes": row.get("Notes", ""),
            }
        )

    return output.getvalue()

DEFICIENCY_STATUS_LABELS = [
    "Missing",
    "Evidence found",
    "Unclear",
]


def filter_deficiency_rows(
    rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Return rows that should appear in a deficiency/follow-up export."""
    return [
        row
        for row in rows
        if any(
            status_label in row.get("Status", "")
            for status_label in DEFICIENCY_STATUS_LABELS
        )
    ]


def build_deficiency_checklist_csv(
    rows: list[dict[str, str]],
) -> str:
    """Build CSV text for unresolved checklist rows only."""
    deficiency_rows = filter_deficiency_rows(rows)

    return build_completeness_checklist_csv(deficiency_rows)