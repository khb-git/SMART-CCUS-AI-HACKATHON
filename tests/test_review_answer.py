from rag.evidence import EvidenceItem
from rag.types import Collection


def make_evidence(evidence_id="E1", collection=Collection.PERMITS):
    return EvidenceItem(
        evidence_id=evidence_id,
        collection=collection,
        source_label=(
            "REGULATORY REFERENCE"
            if collection == Collection.REFERENCE
            else "PERMIT PRECEDENT"
        ),
        source_document="One_Earth_Testing_and_Monitoring_Plan.pdf",
        page_number=63,
        chunk_index=12,
        score=0.7047,
        content_type="text",
        plan_type="testing_monitoring",
        schema_section_id="8",
        schema_section_title="Testing and Monitoring Plan",
        online_link="https://example.com/doc.pdf",
        source_page="https://example.com/docket",
        excerpt="Flow will be monitored with a mass flowmeter at the well head.",
        chunk_id="chunk-123",
    )


def test_split_evidence_by_collection():
    from rag.review_answer import split_evidence_by_collection

    reference = make_evidence("E1", Collection.REFERENCE)
    permit = make_evidence("E2", Collection.PERMITS)

    reference_items, permit_items = split_evidence_by_collection([reference, permit])

    assert reference_items == [reference]
    assert permit_items == [permit]


def test_summarize_evidence_sources():
    from rag.review_answer import summarize_evidence_sources

    item = make_evidence("E1", Collection.PERMITS)

    summary = summarize_evidence_sources([item])

    assert "[E1] PERMIT PRECEDENT" in summary
    assert "One_Earth_Testing_and_Monitoring_Plan.pdf" in summary
    assert "p. 63" in summary
    assert "8 Testing and Monitoring Plan" in summary


def test_build_template_answer_handles_no_evidence():
    from rag.review_answer import build_template_answer

    answer = build_template_answer(
        question="What does the plan say about pressure monitoring?",
        evidence_items=[],
    )

    assert "Insufficient context" in answer.answer
    assert answer.evidence_summary == "No evidence was retrieved."
    assert answer.evidence_items == []


def test_build_template_answer_with_reference_and_permit_evidence():
    from rag.review_answer import build_template_answer

    reference = make_evidence("E1", Collection.REFERENCE)
    permit = make_evidence("E2", Collection.PERMITS)

    answer = build_template_answer(
        question="How should pressure monitoring be reviewed?",
        evidence_items=[reference, permit],
    )

    assert "both regulatory/reference context and permit precedent" in answer.answer
    assert "[E1] REGULATORY REFERENCE" in answer.evidence_summary
    assert "[E2] PERMIT PRECEDENT" in answer.evidence_summary
    assert answer.evidence_items == [reference, permit]


def test_format_review_answer_includes_sections():
    from rag.review_answer import build_template_answer, format_review_answer

    permit = make_evidence("E1", Collection.PERMITS)
    answer = build_template_answer(
        question="How do applicants monitor injection pressure?",
        evidence_items=[permit],
    )

    formatted = format_review_answer(answer)

    assert "Question:" in formatted
    assert "Answer:" in formatted
    assert "Evidence used:" in formatted
    assert "Reviewer interpretation:" in formatted
    assert "Potential follow-up:" in formatted
    assert "Evidence excerpts:" in formatted
    assert "[E1] PERMIT PRECEDENT" in formatted
    assert "Flow will be monitored" in formatted


def test_review_answer_to_dict_is_serializable():
    from rag.review_answer import build_template_answer

    permit = make_evidence("E1", Collection.PERMITS)
    answer = build_template_answer(
        question="How do applicants monitor injection pressure?",
        evidence_items=[permit],
    )

    data = answer.to_dict()

    assert data["question"] == "How do applicants monitor injection pressure?"
    assert data["evidence_items"][0]["evidence_id"] == "E1"
    assert data["evidence_items"][0]["collection"] == "permits"