"""
API client helpers for the Streamlit chatbot UI.
"""

from __future__ import annotations

import os
from typing import Any

import requests

from review.report_export import (
    build_final_review_packet,
    build_markdown_package_report,
    build_markdown_review_report,
    default_package_report_filename,
    default_report_filename,
)


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


def review_document_api(
    file_bytes: bytes,
    filename: str,
    plan_type: str = "auto",
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    api_url: str = DEFAULT_API_URL,
    timeout: int = 240,
) -> dict[str, Any]:
    """Call the backend /review-document endpoint."""
    endpoint = f"{api_url.rstrip('/')}/review-document"

    files = {
        "file": (
            filename,
            file_bytes,
            "application/octet-stream",
        )
    }

    data = {
        "plan_type": plan_type,
        "chunk_size": str(chunk_size),
        "chunk_overlap": str(chunk_overlap),
    }

    response = requests.post(
        endpoint,
        files=files,
        data=data,
        timeout=timeout,
    )

    response.raise_for_status()

    return response.json()

def review_package_api(
    files: list[tuple[str, bytes]],
    package_name: str = "uploaded_package",
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
    api_url: str = DEFAULT_API_URL,
    timeout: int = 600,
) -> dict[str, Any]:
    """Call the backend /review-package endpoint."""
    endpoint = f"{api_url.rstrip('/')}/review-package"

    upload_files = [
        (
            "files",
            (
                filename,
                file_bytes,
                "application/octet-stream",
            ),
        )
        for filename, file_bytes in files
    ]

    data = {
        "package_name": package_name,
        "chunk_size": str(chunk_size),
        "chunk_overlap": str(chunk_overlap),
    }

    response = requests.post(
        endpoint,
        files=upload_files,
        data=data,
        timeout=timeout,
    )

    response.raise_for_status()

    return response.json()

def maip_demo_package_api(
    api_url: str = DEFAULT_API_URL,
    timeout: int = 120,
) -> dict[str, Any]:
    """Call the backend deterministic MAIP demo package endpoint."""
    endpoint = f"{api_url.rstrip('/')}/demo/maip-package"

    response = requests.get(
        endpoint,
        timeout=timeout,
    )

    response.raise_for_status()

    return response.json()

def review_narrative_api(
    package_response: dict[str, Any],
    reviewer_confirmations: list[dict[str, Any]] | None = None,
    use_llm: bool = False,
    model_name: str = "llama3.1",
    api_url: str = DEFAULT_API_URL,
    timeout: int = 240,
) -> dict[str, Any]:
    """Call the backend /review-narrative endpoint."""
    endpoint = f"{api_url.rstrip('/')}/review-narrative"

    payload = {
        "package_response": package_response,
        "reviewer_confirmations": reviewer_confirmations or [],
        "use_llm": use_llm,
        "model_name": model_name,
    }

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

def status_label(status: str) -> str:
    """Format review status labels for display."""
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


def status_icon(status: str) -> str:
    """Return a compact icon for review status."""
    icons = {
        "review_ready": "✅",
        "mostly_complete": "🟡",
        "incomplete": "🟠",
        "needs_revision": "🔴",
        "present": "✅",
        "evidence_found": "🟡",
        "missing": "🔴",
        "unclear": "⚪",
    }

    return icons.get(str(status or ""), "ℹ️")