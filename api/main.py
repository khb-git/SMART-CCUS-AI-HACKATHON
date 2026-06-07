"""
FastAPI backend for the Class VI review assistant.
"""

from pathlib import Path
import shutil
import tempfile
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from rag.ask import ask_question
from review.document_classifier import classify_review_document
from review.gap_analysis import analyze_document_against_checklist
from review.schema import load_default_checklist
from review.temp_ingestion import (
    ingest_review_document_temporarily,
    is_supported_review_file,
)


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

class ReviewDocumentResponse(BaseModel):
    """Response body for uploaded document review."""

    document_name: str
    document_type: str
    classification_confidence: str
    classification: dict[str, Any]
    report: dict[str, Any]
    storage_policy: str

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

@app.post("/review-document", response_model=ReviewDocumentResponse)
def review_document(
    file: UploadFile = File(...),
    plan_type: str = Form("auto"),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(100),
):
    """Temporarily review an uploaded Class VI document for completeness."""
    filename = file.filename or ""

    if not filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")

    if not is_supported_review_file(filename):
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported review file type. Supported types are PDF, DOCX, and XLSX."
            ),
        )

    with tempfile.TemporaryDirectory() as upload_temp_dir:
        upload_path = Path(upload_temp_dir) / Path(filename).name

        with upload_path.open("wb") as output_file:
            shutil.copyfileobj(file.file, output_file)

        temporary_document = ingest_review_document_temporarily(
            upload_path,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    classification = classify_review_document(temporary_document)

    selected_plan_type = (
        classification.document_type
        if plan_type == "auto"
        else plan_type
    )

    if selected_plan_type == "unknown":
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not classify uploaded document. Please specify a supported "
                "plan_type manually."
            ),
        )

    try:
        checklist = load_default_checklist(selected_plan_type)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"No review checklist is available for plan_type: {selected_plan_type}",
        ) from exc

    report = analyze_document_against_checklist(
        temporary_document,
        checklist,
    )

    return {
        "document_name": temporary_document.original_filename,
        "document_type": selected_plan_type,
        "classification_confidence": classification.confidence,
        "classification": classification.to_dict(),
        "report": report.to_dict(),
        "storage_policy": (
            "Uploaded documents are processed temporarily for this review request "
            "and are not stored in permanent data folders or Chroma collections."
        ),
    }