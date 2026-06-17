"""
FastAPI backend for the Class VI review assistant.
"""

from pathlib import Path
import shutil
import tempfile
from typing import Annotated, Any

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

from review.package_review import review_document_package

from demo_samples.maip_demo_package import (
    build_maip_demo_final_review_packet,
    build_maip_demo_markdown_report,
    build_maip_demo_package_response,
)

from review.llm_narrative import (
    LlmNarrativeInput,
    build_review_narrative,
)
from review.report_export import (
    collect_completeness_checklist_rows,
    collect_reviewer_action_items,
    package_review_metrics,
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

class ReviewPackageResponse(BaseModel):
    """Response body for uploaded package review."""

    package_name: str
    report: dict[str, Any]
    storage_policy: str

class DemoMarkdownResponse(BaseModel):
    """Response body for deterministic demo Markdown outputs."""

    package_name: str
    markdown: str
    storage_policy: str

class LlmNarrativeRequest(BaseModel):
    """Request body for optional LLM reviewer narrative."""

    package_response: dict[str, Any]
    reviewer_confirmations: list[dict[str, Any]] = Field(default_factory=list)
    use_llm: bool = False
    model_name: str = "llama3.1"


class LlmNarrativeResponse(BaseModel):
    """Response body for optional LLM reviewer narrative."""

    narrative: str
    model_name: str
    used_llm: bool
    boundary_notice: str

@app.get("/health")
def health():
    """Simple health check."""
    return {
        "status": "ok",
        "service": "class-vi-review-assistant",
    }


@app.get("/demo/maip-package", response_model=ReviewPackageResponse)
def maip_demo_package():
    """Return a deterministic MAIP demo package review response."""
    return build_maip_demo_package_response()


@app.get("/demo/maip-package/report", response_model=DemoMarkdownResponse)
def maip_demo_package_report():
    """Return the deterministic MAIP demo Markdown package report."""
    return {
        "package_name": "maip_demo_package",
        "markdown": build_maip_demo_markdown_report(),
        "storage_policy": "Demo fixture only. No uploaded files are processed.",
    }


@app.get("/demo/maip-package/final-packet", response_model=DemoMarkdownResponse)
def maip_demo_final_review_packet():
    """Return the deterministic MAIP demo final review packet."""
    return {
        "package_name": "maip_demo_package",
        "markdown": build_maip_demo_final_review_packet(),
        "storage_policy": "Demo fixture only. No uploaded files are processed.",
    }

@app.post("/review-narrative", response_model=LlmNarrativeResponse)
def review_narrative(request: LlmNarrativeRequest):
    """Generate an optional reviewer narrative over deterministic findings."""
    narrative_input = build_narrative_input_from_package_response(
        package_response=request.package_response,
        reviewer_confirmations=request.reviewer_confirmations,
    )
    narrative_result = build_review_narrative(
        narrative_input,
        use_llm=request.use_llm,
        model_name=request.model_name,
    )

    return narrative_result.to_dict()

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

@app.post("/review-package", response_model=ReviewPackageResponse)
def review_package(
    files: Annotated[
        list[UploadFile],
        File(
            description="Upload one or more Class VI package documents.",
            json_schema_extra={
                "items": {
                    "type": "string",
                    "format": "binary",
                }
            },
        ),
    ],
    package_name: Annotated[str, Form()] = "uploaded_package",
    chunk_size: Annotated[int, Form()] = 1000,
    chunk_overlap: Annotated[int, Form()] = 100,
):
    """Temporarily review a multi-document Class VI package."""
    if not files:
        raise HTTPException(
            status_code=400,
            detail="At least one file must be uploaded.",
        )

    temporary_documents = []

    with tempfile.TemporaryDirectory() as upload_temp_dir:
        upload_temp_path = Path(upload_temp_dir)

        for uploaded_file in files:
            filename = uploaded_file.filename or ""

            if not filename:
                raise HTTPException(
                    status_code=400,
                    detail="Each uploaded file must have a filename.",
                )

            if not is_supported_review_file(filename):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Unsupported review file type for {filename}. "
                        "Supported types are PDF, DOCX, and XLSX."
                    ),
                )

            upload_path = upload_temp_path / Path(filename).name

            with upload_path.open("wb") as output_file:
                shutil.copyfileobj(uploaded_file.file, output_file)

            try:
                temporary_document = ingest_review_document_temporarily(
                    upload_path,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                )
            except Exception as exc:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Temporary review ingestion failed for {filename}: "
                        f"{type(exc).__name__}: {exc}"
                    ),
                ) from exc

            temporary_documents.append(temporary_document)

    try:
        report = review_document_package(
            temporary_documents,
            package_name=package_name,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Package review failed: {type(exc).__name__}: {exc}",
        ) from exc

    return {
        "package_name": package_name,
        "report": report.to_dict(),
        "storage_policy": (
            "Uploaded package documents are processed temporarily for this review "
            "request and are not stored in permanent data folders or Chroma collections."
        ),
    }

def package_counts_from_report(package_report: dict[str, Any]) -> dict[str, Any]:
    """Return exact package counts for grounded reviewer narratives."""
    detected_document_types = package_report.get("detected_plan_types", []) or []
    missing_required = package_report.get("missing_required_plan_types", []) or []
    missing_expected = package_report.get("missing_expected_plan_types", []) or []
    supporting_documents = package_report.get("supporting_documents", []) or []
    duplicate_plan_types = package_report.get("duplicate_plan_types", []) or []
    unknown_documents = package_report.get("unknown_documents", []) or []

    return {
        "detected_document_types_count": len(detected_document_types),
        "missing_required_document_types_count": len(missing_required),
        "missing_expected_document_types_count": len(missing_expected),
        "supporting_documents_count": len(supporting_documents),
        "duplicate_document_types_count": len(duplicate_plan_types),
        "unknown_documents_count": len(unknown_documents),
        "detected_document_types": detected_document_types,
        "missing_required_document_types": missing_required,
        "missing_expected_document_types": missing_expected,
        "supporting_documents": supporting_documents,
        "duplicate_document_types": duplicate_plan_types,
        "unknown_documents": unknown_documents,
    }

def build_narrative_input_from_package_response(
    package_response: dict[str, Any],
    reviewer_confirmations: list[dict[str, Any]] | None = None,
) -> LlmNarrativeInput:
    """Build deterministic LLM narrative input from a package response."""
    reviewer_confirmations = reviewer_confirmations or []
    package_report = package_response.get("report", {}) or {}

    checklist_rows = collect_completeness_checklist_rows(package_report)
    priority_rows = [
        row
        for row in checklist_rows
        if row.get("status") in {"missing", "evidence_found", "unclear"}
    ][:12]

    return LlmNarrativeInput(
        package_name=package_response.get(
            "package_name",
            package_report.get("package_name", "uploaded_package"),
        ),
        overall_status=package_report.get("overall_status", "unknown"),
        summary=package_report.get("summary", ""),
        package_metrics=package_review_metrics(package_report),
        package_counts=package_counts_from_report(package_report),
        reviewer_action_items=collect_reviewer_action_items(package_report),
        priority_checklist_rows=priority_rows,
        maip_validation=package_report.get("maip_validation") or {},
        reviewer_confirmations=reviewer_confirmations,
    )