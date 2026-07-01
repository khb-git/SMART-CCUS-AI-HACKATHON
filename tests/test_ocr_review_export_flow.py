from review.temp_ingestion import TemporaryReviewChunk, TemporaryReviewDocument


def finding_by_id(report):
    return {
        finding.item_id: finding
        for finding in report.findings
    }


def make_ocr_testing_monitoring_document():
    return TemporaryReviewDocument(
        original_filename="ocr_testing_monitoring_plan.pdf",
        file_extension=".pdf",
        chunks=[
            TemporaryReviewChunk(
                text=(
                    "Table evidence | page 6 | image OCR\n"
                    "Table row: Parameter | Equipment | Frequency | Recording | Location\n"
                    "Table row: Injection pressure | pressure transducer | continuous recording | SCADA | wellhead\n"
                ),
                metadata={
                    "content_type": "image_ocr",
                    "source_type": "image_ocr",
                    "page_number": 6,
                    "chunk_index": 0,
                    "ocr_confidence": "Low",
                    "redaction_detected": False,
                    "reviewer_note": (
                        "This evidence was extracted from image/OCR content "
                        "and should be verified against the source page."
                    ),
                },
            )
        ],
    )


def test_ocr_chunk_flows_into_gap_analysis_evidence_locations():
    from review.gap_analysis import analyze_document_against_checklist
    from review.schema import load_default_checklist

    document = make_ocr_testing_monitoring_document()
    checklist = load_default_checklist("testing_monitoring")

    report = analyze_document_against_checklist(document, checklist)
    findings = finding_by_id(report)

    finding = findings["injection_pressure_monitoring"]

    assert finding.status.value == "present"
    assert finding.evidence_locations

    location = finding.evidence_locations[0]

    assert location.file_name == "ocr_testing_monitoring_plan.pdf"
    assert location.page_number == 6
    assert location.chunk_index == 0
    assert location.content_type == "image_ocr"
    assert "injection pressure" in location.matched_terms
    assert "pressure transducer" in location.matched_terms
    assert "continuous recording" in location.matched_terms


def test_ocr_gap_analysis_evidence_exports_to_markdown_report():
    from review.gap_analysis import analyze_document_against_checklist
    from review.report_export import build_markdown_review_report
    from review.schema import load_default_checklist

    document = make_ocr_testing_monitoring_document()
    checklist = load_default_checklist("testing_monitoring")

    report = analyze_document_against_checklist(document, checklist)

    review_response = {
        "document_name": document.original_filename,
        "document_type": "testing_monitoring",
        "classification_confidence": "high",
        "classification": {
            "document_type": "testing_monitoring",
            "confidence": "high",
            "matched_terms": ["testing and monitoring plan"],
            "reason": "Synthetic OCR regression document.",
        },
        "report": report.to_dict(),
        "storage_policy": (
            "Uploaded documents are processed temporarily for this review request "
            "and are not stored in permanent data folders or Chroma collections."
        ),
    }

    markdown = build_markdown_review_report(review_response)

    assert "# Class VI Document Review Report" in markdown
    assert "ocr_testing_monitoring_plan.pdf" in markdown
    assert "### Present — Injection pressure monitoring" in markdown
    assert "**Evidence locations:**" in markdown
    assert "Image OCR" in markdown
    assert "page" not in markdown.lower() or "6" in markdown
    assert "This evidence was extracted from image/OCR content" in markdown
    assert "pressure transducer" in markdown
    assert "continuous recording" in markdown


def test_redacted_ocr_evidence_location_exports_warning_without_inference():
    from review.report_export import build_markdown_review_report

    review_response = {
        "document_name": "redacted_testing_monitoring_plan.pdf",
        "document_type": "testing_monitoring",
        "classification_confidence": "high",
        "classification": {
            "document_type": "testing_monitoring",
            "confidence": "high",
            "matched_terms": ["testing and monitoring plan"],
            "reason": "Synthetic redacted OCR regression document.",
        },
        "report": {
            "document_name": "redacted_testing_monitoring_plan.pdf",
            "plan_type": "testing_monitoring",
            "checklist_id": "testing_monitoring_v1",
            "overall_status": "mostly_complete",
            "summary": "Synthetic report with redacted OCR evidence.",
            "findings": [
                {
                    "item_id": "injection_pressure_monitoring",
                    "label": "Injection pressure monitoring",
                    "status": "evidence_found",
                    "severity": "critical",
                    "requirement_level": "required",
                    "matched_terms": ["injection pressure"],
                    "supporting_excerpts": [
                        "Sensitive, Confidential, or Privileged Information. Injection pressure monitoring."
                    ],
                    "finding": (
                        "Injection pressure monitoring: evidence found, but reviewer "
                        "confirmation is recommended."
                    ),
                    "recommended_fix": "Confirm the unredacted source document before crediting this evidence.",
                    "confidence": "Low",
                    "evidence_locations": [
                        {
                            "file_name": "redacted_testing_monitoring_plan.pdf",
                            "page_number": 3,
                            "chunk_index": 0,
                            "content_type": "redacted_image_ocr",
                            "source_type": "redacted_image_ocr",
                            "excerpt": (
                                "Sensitive, Confidential, or Privileged Information. "
                                "Injection pressure monitoring."
                            ),
                            "matched_terms": ["injection pressure"],
                            "redaction_detected": True,
                        }
                    ],
                }
            ],
        },
        "storage_policy": "Temporary review only.",
    }

    markdown = build_markdown_review_report(review_response)

    assert "Redacted image OCR" in markdown
    assert "cannot inspect or infer hidden content" in markdown
    assert "Confirm the unredacted source document" in markdown