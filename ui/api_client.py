"""
API client helpers for the Streamlit chatbot UI.
"""

from __future__ import annotations

import os
from typing import Any

import requests


DEFAULT_API_URL = os.getenv("SMART_CCUS_API_URL", "http://127.0.0.1:8000")


def build_ask_payload(
    query: str,
    persist_directory: str = "chroma_data",
    section_id: str = "",
    intent: str = "auto",
    k_reference: int = 3,
    k_permits: int = 5,
    fetch_k: int = 30,
    max_per_source: int = 1,
    expand_retrieval_query: bool = True,
    use_reranking: bool = True,
) -> dict[str, Any]:
    """Build the POST /ask request payload."""
    return {
        "query": query,
        "persist_directory": persist_directory,
        "section_id": section_id,
        "intent": intent,
        "k_reference": k_reference,
        "k_permits": k_permits,
        "fetch_k": fetch_k,
        "max_per_source": max_per_source,
        "expand_retrieval_query": expand_retrieval_query,
        "use_reranking": use_reranking,
    }


def ask_api(
    payload: dict[str, Any],
    api_url: str = DEFAULT_API_URL,
    timeout: int = 180,
) -> dict[str, Any]:
    """Call the backend /ask endpoint."""
    endpoint = f"{api_url.rstrip('/')}/ask"

    response = requests.post(
        endpoint,
        json=payload,
        timeout=timeout,
    )

    response.raise_for_status()

    return response.json()


def format_similarity_score(value) -> str:
    """Format a retrieval similarity score for display."""
    if value is None or value == "":
        return "N/A"

    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return str(value)


def format_evidence_heading(item: dict[str, Any]) -> str:
    """Create a compact evidence card heading."""
    evidence_id = item.get("evidence_id", "E?")
    source_label = item.get("source_label", "EVIDENCE")
    source_document = item.get("source_document", "Unknown source")
    page_number = item.get("page_number", "")

    page_text = f", p. {page_number}" if page_number else ""

    return f"[{evidence_id}] {source_label}: {source_document}{page_text}"