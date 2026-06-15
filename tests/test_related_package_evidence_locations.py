from review.package_review import (
    PackageDocumentReview,
    build_related_package_evidence_for_finding,
)
from review.temp_ingestion import TemporaryReviewChunk, TemporaryReviewDocument


def test_related_package_evidence_includes_location_details():
    source_document = TemporaryReviewDocument(
        original_filename="ADM_Financial_Responsibility.pdf",
        file_extension=".pdf",
        chunks=[
            TemporaryReviewChunk(
                text="This document does not include the financial instrument.",
                metadata={
                    "page": 1,
                    "chunk_index": 0,
                    "content_type": "text",
                },
            )
        ],
    )

    related_document = TemporaryReviewDocument(
        original_filename="ADM_Project_Narrative.pdf",
        file_extension=".pdf",
        chunks=[
            TemporaryReviewChunk(
                text=(
                    "The project narrative references financial responsibility, "
                    "financial assurance, and cost estimate information for closure."
                ),
                metadata={
                    "page": 7,
                    "chunk_index": 2,
                    "content_type": "text",
                    "section_heading": "Financial Responsibility Summary",
                },
            )
        ],
    )

    source_review = PackageDocumentReview(
        document_name="ADM_Financial_Responsibility.pdf",
        document_type="financial_responsibility",
        classification_confidence="high",
        classification={},
    )

    related_review = PackageDocumentReview(
        document_name="ADM_Project_Narrative.pdf",
        document_type="project_narrative",
        classification_confidence="high",
        classification={},
    )

    finding = {
        "item_id": "financial_instrument",
        "label": "Financial instrument",
        "status": "missing",
        "severity": "critical",
        "requirement_level": "required",
        "matched_terms": [],
    }

    related_evidence = build_related_package_evidence_for_finding(
        source_document_name=source_document.original_filename,
        plan_type="financial_responsibility",
        finding=finding,
        package_documents=[source_document, related_document],
        document_reviews=[source_review, related_review],
    )

    assert related_evidence

    first_row = related_evidence[0]

    assert first_row["document_name"] == "ADM_Project_Narrative.pdf"
    assert first_row["document_type"] == "project_narrative"
    assert first_row["evidence_source"] == "cross_document_text"
    assert first_row["page_number"] == 7
    assert first_row["chunk_index"] == 2
    assert first_row["content_type"] == "text"
    assert first_row["section_heading"] == "Financial Responsibility Summary"
    assert first_row["excerpt"]
    assert "financial responsibility" in first_row["matched_terms"]
    assert "financial assurance" in first_row["matched_terms"]