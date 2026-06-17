"""Optional LLM reviewer narrative layer.

The deterministic backend remains the source of truth.

Architecture:
    Backend decides.
    Reviewer confirms.
    LLM explains.

This module builds prompts and optional local-LLM narratives from deterministic
package review outputs. It must not change checklist statuses, MAIP statuses,
severity, regulatory citations, evidence locations, or reviewer confirmations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


LLM_BOUNDARY_NOTICE = (
    "Backend decides. Reviewer confirms. LLM explains. "
    "The following narrative is generated from deterministic backend findings. "
    "It does not change status, severity, citations, evidence locations, or "
    "reviewer disposition. A qualified reviewer should confirm the findings."
)


@dataclass
class LlmNarrativeInput:
    """Compact deterministic input for an LLM reviewer narrative."""

    package_name: str
    overall_status: str
    summary: str
    reviewer_action_items: list[str]
    priority_checklist_rows: list[dict[str, Any]]
    maip_validation: dict[str, Any]
    reviewer_confirmations: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable narrative input."""
        return {
            "package_name": self.package_name,
            "overall_status": self.overall_status,
            "summary": self.summary,
            "reviewer_action_items": self.reviewer_action_items,
            "priority_checklist_rows": self.priority_checklist_rows,
            "maip_validation": self.maip_validation,
            "reviewer_confirmations": self.reviewer_confirmations,
        }


@dataclass
class LlmNarrativeResult:
    """Narrative result and metadata."""

    narrative: str
    model_name: str
    used_llm: bool
    boundary_notice: str = LLM_BOUNDARY_NOTICE

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable narrative result."""
        return {
            "narrative": self.narrative,
            "model_name": self.model_name,
            "used_llm": self.used_llm,
            "boundary_notice": self.boundary_notice,
        }


def compact_text(value: Any, max_chars: int = 500) -> str:
    """Return compact text safe for prompt inclusion."""
    text = " ".join(str(value or "").split())

    if len(text) <= max_chars:
        return text

    return text[: max_chars - 3].rstrip() + "..."


def maip_supporting_value_text(value: dict[str, Any]) -> str:
    """Format one MAIP supporting value for narrative context."""
    concept = value.get("concept", "value")
    numeric_value = value.get("value")
    unit = value.get("unit", "")
    source_file = value.get("source_file", "")
    page_number = value.get("page_number")

    parts = [str(concept)]

    if numeric_value is not None:
        parts.append(f"{numeric_value} {unit}".strip())

    location = source_file

    if page_number not in {"", None}:
        location = f"{location}, page {page_number}" if location else f"page {page_number}"

    if location:
        parts.append(f"({location})")

    return " ".join(part for part in parts if part)


def maip_findings_for_prompt(maip_validation: dict[str, Any]) -> list[str]:
    """Format MAIP findings for LLM prompt context."""
    lines = []

    for finding in maip_validation.get("findings", []) or []:
        supporting_values = finding.get("supporting_values", []) or []
        supporting_text = "; ".join(
            maip_supporting_value_text(value)
            for value in supporting_values
        ) or "No supporting values."

        lines.append(
            "- "
            f"{finding.get('finding_id', 'maip_finding')}: "
            f"status={finding.get('status', '')}; "
            f"severity={finding.get('severity', '')}; "
            f"message={compact_text(finding.get('message', ''))}; "
            f"supporting_values={compact_text(supporting_text, max_chars=700)}"
        )

    return lines


def checklist_rows_for_prompt(rows: list[dict[str, Any]]) -> list[str]:
    """Format priority checklist rows for LLM prompt context."""
    lines = []

    for row in rows:
        lines.append(
            "- "
            f"status={row.get('status', row.get('Status', ''))}; "
            f"required_item={compact_text(row.get('required_item', row.get('Required Item', '')))}; "
            f"module={compact_text(row.get('module_folder', row.get('GSDT Module/Folder', '')))}; "
            f"citation={compact_text(row.get('regulatory_citation', row.get('Regulatory Citation', '')))}; "
            f"file={compact_text(row.get('file_name', row.get('File Name', '')))}; "
            f"page={compact_text(row.get('page_number', row.get('Page Number', '')))}; "
            f"notes={compact_text(row.get('notes', row.get('Notes', '')), max_chars=700)}"
        )

    return lines


def build_llm_narrative_prompt(narrative_input: LlmNarrativeInput) -> str:
    """Build a constrained prompt for reviewer narrative generation."""
    maip_validation = narrative_input.maip_validation or {}
    priority_rows = narrative_input.priority_checklist_rows or []

    action_items = narrative_input.reviewer_action_items or [
        "Confirm deterministic findings before final disposition."
    ]

    prompt_lines = [
        "You are assisting with a Class VI carbon storage permit package review.",
        "",
        "Important boundary:",
        "- Backend decides.",
        "- Reviewer confirms.",
        "- LLM explains.",
        "- Do not change statuses, severities, citations, page numbers, or evidence.",
        "- Do not invent evidence.",
        "- Do not state final compliance approval.",
        "",
        "Write a concise reviewer narrative using only the deterministic input below.",
        "Use this structure:",
        "1. Package-level summary",
        "2. Key reviewer action items",
        "3. MAIP cross-reference interpretation",
        "4. Checklist evidence interpretation",
        "5. Recommended reviewer next steps",
        "",
        "Deterministic package summary:",
        f"- Package name: {narrative_input.package_name}",
        f"- Overall status: {narrative_input.overall_status}",
        f"- Summary: {compact_text(narrative_input.summary, max_chars=900)}",
        "",
        "Reviewer action items:",
    ]

    prompt_lines.extend(f"- {compact_text(item)}" for item in action_items)

    prompt_lines.extend(
        [
            "",
            "MAIP validation:",
            f"- Overall MAIP status: {maip_validation.get('overall_status', 'unknown')}",
            f"- Summary: {compact_text(maip_validation.get('summary', ''), max_chars=900)}",
        ]
    )

    prompt_lines.extend(maip_findings_for_prompt(maip_validation))

    prompt_lines.extend(
        [
            "",
            "Priority checklist rows:",
        ]
    )

    checklist_lines = checklist_rows_for_prompt(priority_rows)

    if checklist_lines:
        prompt_lines.extend(checklist_lines)
    else:
        prompt_lines.append("- No priority checklist rows were provided.")

    if narrative_input.reviewer_confirmations:
        prompt_lines.extend(
            [
                "",
                "Reviewer confirmations and notes:",
            ]
        )

        for row in narrative_input.reviewer_confirmations[:20]:
            prompt_lines.append(
                "- "
                f"confirmation={compact_text(row.get('Reviewer Confirmation', ''))}; "
                f"item={compact_text(row.get('Required Item', row.get('Finding', '')))}; "
                f"notes={compact_text(row.get('Reviewer Notes', ''), max_chars=500)}"
            )

    prompt_lines.extend(
        [
            "",
            "Return only the reviewer narrative. Do not return JSON.",
        ]
    )

    return "\n".join(prompt_lines)


def build_template_review_narrative(
    narrative_input: LlmNarrativeInput,
) -> str:
    """Build a deterministic fallback reviewer narrative."""
    maip_validation = narrative_input.maip_validation or {}
    maip_status = maip_validation.get("overall_status", "unknown")
    priority_rows = narrative_input.priority_checklist_rows or []

    lines = [
        LLM_BOUNDARY_NOTICE,
        "",
        "### Package-level summary",
        (
            f"The package `{narrative_input.package_name}` has backend status "
            f"`{narrative_input.overall_status}`. "
            f"{compact_text(narrative_input.summary, max_chars=900)}"
        ),
        "",
        "### Key reviewer action items",
    ]

    for action_item in narrative_input.reviewer_action_items or []:
        lines.append(f"- {action_item}")

    if not narrative_input.reviewer_action_items:
        lines.append("- Confirm deterministic findings before final disposition.")

    lines.extend(
        [
            "",
            "### MAIP cross-reference interpretation",
            (
                f"The deterministic MAIP validator returned `{maip_status}`. "
                f"{compact_text(maip_validation.get('summary', ''), max_chars=900)}"
            ),
        ]
    )

    for finding_line in maip_findings_for_prompt(maip_validation)[:7]:
        lines.append(finding_line)

    lines.extend(
        [
            "",
            "### Checklist evidence interpretation",
        ]
    )

    if priority_rows:
        for row_line in checklist_rows_for_prompt(priority_rows[:8]):
            lines.append(row_line)
    else:
        lines.append("- No priority checklist rows were provided.")

    lines.extend(
        [
            "",
            "### Recommended reviewer next steps",
            (
                "Confirm the cited source files, page numbers, and evidence excerpts. "
                "Treat evidence-found rows as reviewer-confirmation items, not automatic "
                "final approvals. Use reviewer notes to document any follow-up needed."
            ),
        ]
    )

    return "\n".join(lines)


def try_generate_ollama_narrative(
    prompt: str,
    model_name: str = "llama3.1",
    temperature: float = 0.1,
) -> str:
    """Generate an optional local Ollama narrative.

    Raises ImportError or runtime exceptions when Ollama/LangChain is unavailable.
    Callers should catch these exceptions and fall back to the deterministic template.
    """
    from langchain_ollama import ChatOllama

    llm = ChatOllama(
        model=model_name,
        temperature=temperature,
    )
    response = llm.invoke(prompt)

    return str(getattr(response, "content", response)).strip()


def build_review_narrative(
    narrative_input: LlmNarrativeInput,
    *,
    use_llm: bool = False,
    model_name: str = "llama3.1",
) -> LlmNarrativeResult:
    """Build a reviewer narrative from deterministic package findings."""
    prompt = build_llm_narrative_prompt(narrative_input)

    if use_llm:
        try:
            narrative = try_generate_ollama_narrative(
                prompt=prompt,
                model_name=model_name,
            )
        except Exception:
            narrative = build_template_review_narrative(narrative_input)
            return LlmNarrativeResult(
                narrative=narrative,
                model_name="deterministic-template-fallback",
                used_llm=False,
            )

        if narrative:
            return LlmNarrativeResult(
                narrative=LLM_BOUNDARY_NOTICE + "\n\n" + narrative,
                model_name=model_name,
                used_llm=True,
            )

    return LlmNarrativeResult(
        narrative=build_template_review_narrative(narrative_input),
        model_name="deterministic-template",
        used_llm=False,
    )