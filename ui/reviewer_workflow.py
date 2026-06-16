"""Reviewer workflow helpers for the Streamlit package review UI."""

from __future__ import annotations

import csv
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


def append_reviewer_confirmation_export(
    markdown_report: str,
    rows: list[dict[str, str]],
) -> str:
    """Append reviewer confirmation export rows to a Markdown package report."""
    section = build_reviewer_confirmation_export_section(rows)
    return markdown_report.rstrip() + "\n\n" + section.rstrip() + "\n"


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
                "File Name": row.get("File Name", ""),
                "Page Number": row.get("Page Number", ""),
                "Notes": row.get("Notes", ""),
            }
        )

    return output.getvalue()