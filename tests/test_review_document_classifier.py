from review.temp_ingestion import TemporaryReviewChunk, TemporaryReviewDocument


def make_document(filename="document.pdf", text=""):
    return TemporaryReviewDocument(
        original_filename=filename,
        file_extension=".pdf",
        chunks=[
            TemporaryReviewChunk(
                text=text,
                metadata={"content_type": "text"},
            )
        ],
    )


def test_classify_testing_monitoring_document_from_text():
    from review.document_classifier import classify_review_document

    document = make_document(
        filename="uploaded.pdf",
        text=(
            "Testing and Monitoring Plan. Continuous recording devices will monitor "
            "injection pressure, injection rate, annular pressure, and flow rate."
        ),
    )

    classification = classify_review_document(document)

    assert classification.document_type == "testing_monitoring"
    assert classification.confidence == "high"
    assert "testing and monitoring plan" in classification.matched_terms


def test_classify_testing_monitoring_document_from_filename():
    from review.document_classifier import classify_review_document

    document = make_document(
        filename="testing_monitoring_plan.docx",
        text="Uploaded document.",
    )

    classification = classify_review_document(document)

    assert classification.document_type == "testing_monitoring"
    assert classification.confidence in {"medium", "high"}


def test_classify_aor_corrective_action_document():
    from review.document_classifier import classify_review_document

    document = make_document(
        filename="aor_ca_plan.pdf",
        text=(
            "Area of Review and Corrective Action Plan. The plan evaluates legacy wells "
            "and artificial penetrations."
        ),
    )

    classification = classify_review_document(document)

    assert classification.document_type == "aor_corrective_action"
    assert classification.confidence == "high"


def test_classify_emergency_response_document():
    from review.document_classifier import classify_review_document

    document = make_document(
        filename="err_plan.pdf",
        text="Emergency and Remedial Response Plan with notification and shut-in procedures.",
    )

    classification = classify_review_document(document)

    assert classification.document_type == "emergency_remedial_response"
    assert classification.confidence == "high"


def test_classify_unknown_document():
    from review.document_classifier import classify_review_document

    document = make_document(
        filename="random_notes.pdf",
        text="This is a random document about meeting logistics.",
    )

    classification = classify_review_document(document)

    assert classification.document_type == "unknown"
    assert classification.confidence == "unknown"
    assert classification.matched_terms == []


def test_classification_to_dict_is_serializable():
    from review.document_classifier import classify_review_document

    document = make_document(
        filename="financial_responsibility.pdf",
        text="Financial Responsibility Demonstration with cost estimate and surety bond.",
    )

    classification = classify_review_document(document)
    data = classification.to_dict()

    assert data["document_type"] == "financial_responsibility"
    assert data["confidence"] == "high"
    assert data["matched_terms"]
    assert data["reason"]