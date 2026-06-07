"""
FastAPI backend for the Class VI review assistant.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from rag.ask import ask_question


app = FastAPI(
    title="SMART CCUS Class VI Review Assistant",
    version="0.1.0",
    description="Backend API for Class VI permit review question answering.",
)


class AskRequest(BaseModel):
    """Request body for the ask endpoint."""

    query: str = Field(..., min_length=1)
    persist_directory: str = "./chroma_data"
    model_name: str | None = None
    section_id: str = ""
    k_reference: int = 3
    k_permits: int = 5
    fetch_k: int = 30
    max_per_source: int = 1
    intent: str = "auto"
    expand_retrieval_query: bool = True
    use_reranking: bool = True


class AskResponse(BaseModel):
    """Response body for the ask endpoint."""

    question: str
    answer: str
    evidence_summary: str
    reviewer_interpretation: str
    potential_follow_up: str
    evidence_items: list[dict[str, Any]]


@app.get("/health")
def health():
    """Simple health check."""
    return {
        "status": "ok",
        "service": "class-vi-review-assistant",
    }


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """Answer a Class VI review question."""
    kwargs = {
        "question": request.query,
        "persist_directory": request.persist_directory,
        "section_id": request.section_id,
        "k_reference": request.k_reference,
        "k_permits": request.k_permits,
        "fetch_k": request.fetch_k,
        "max_per_source": request.max_per_source,
        "intent": request.intent,
        "expand_retrieval_query": request.expand_retrieval_query,
        "use_reranking": request.use_reranking,
    }

    if request.model_name:
        kwargs["model_name"] = request.model_name

    review_answer = ask_question(**kwargs)

    return review_answer.to_dict()