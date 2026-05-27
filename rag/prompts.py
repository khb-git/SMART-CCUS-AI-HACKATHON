"""
Prompt templates for Class VI permit review.

Templates label reference (rules) and permit (precedent) context distinctly
so the model knows which is authoritative.
"""

SYSTEM_PROMPT = """You are an expert reviewer of EPA Class VI Underground \
Injection Control permit applications for geologic CO2 sequestration. \
You evaluate applications against 40 CFR Part 146 Subpart H and precedent \
from approved applications.

Rules:
- Cite specific CFR provisions when identifying deficiencies.
- Distinguish what the regulation requires from what approved applicants have done.
- If the provided context is insufficient, say "Insufficient context to determine" \
rather than guess.
- Quote section IDs (e.g. Section 7.2) when referring to permit content.
"""


def format_context(reference_results, permit_results):
    """Render retrieval results into a labeled context block."""
    parts = []
    if reference_results:
        parts.append("=== REGULATORY REFERENCE (authoritative) ===")
        for i, r in enumerate(reference_results, 1):
            cite = r.chunk.metadata.cfr_citation or "uncited"
            parts.append(f"[REF-{i}] ({cite}) {r.chunk.text}")
    if permit_results:
        parts.append("\n=== PERMIT PRECEDENT (approved applications) ===")
        for i, r in enumerate(permit_results, 1):
            project = r.chunk.metadata.project_name or "unknown"
            section = r.chunk.metadata.subsection_id or r.chunk.metadata.section_id or "?"
            parts.append(f"[PERM-{i}] ({project}, Section {section}) {r.chunk.text}")
    return "\n".join(parts) if parts else "No relevant context retrieved."


def build_review_prompt(question, reference_results, permit_results):
    """Build the full prompt for a review question."""
    context = format_context(reference_results, permit_results)
    return f"""{SYSTEM_PROMPT}

Context:
{context}

Question: {question}

Answer:"""
