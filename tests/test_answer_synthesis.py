from rag.evidence import EvidenceItem
from rag.types import Collection


def make_evidence(
    evidence_id="E1",
    collection=Collection.PERMITS,
    excerpt="Flow will be monitored with a mass flowmeter at the well head.",
):
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
        excerpt=excerpt,
        chunk_id="chunk-123",
    )


def test_tokenize_removes_stopwords():
    from rag.answer_synthesis import tokenize

    tokens = tokenize("How do applicants monitor injection pressure and flow rate?")

    assert "how" not in tokens
    assert "applicants" in tokens
    assert "monitor" in tokens
    assert "injection" in tokens
    assert "pressure" in tokens


def test_split_sentences_handles_excerpt_text():
    from rag.answer_synthesis import split_sentences

    sentences = split_sentences(
        "Flow will be monitored with a mass flowmeter. "
        "The meter will be calibrated across the expected range."
    )

    assert len(sentences) == 2
    assert sentences[0].startswith("Flow will be monitored")


def test_extract_relevant_sentences_selects_question_relevant_sentence():
    from rag.answer_synthesis import extract_relevant_sentences

    evidence = [
        make_evidence(
            excerpt=(
                "The project will submit annual reports. "
                "Flow will be monitored with a mass flowmeter at the well head. "
                "The office address is listed in the application."
            )
        )
    ]

    sentences = extract_relevant_sentences(
        question="How do applicants monitor flow rate?",
        evidence_items=evidence,
        max_sentences=1,
    )

    assert len(sentences) == 1
    assert "Flow will be monitored" in sentences[0].sentence
    assert sentences[0].evidence_id == "E1"


def test_build_evidence_grounded_answer_uses_evidence_ids():
    from rag.answer_synthesis import build_evidence_grounded_answer

    evidence = [
        make_evidence(
            "E1",
            Collection.PERMITS,
            "Flow will be monitored with a mass flowmeter at the well head.",
        ),
        make_evidence(
            "E2",
            Collection.PERMITS,
            "Continuous recording devices will monitor injection pressure and temperature.",
        ),
    ]

    answer = build_evidence_grounded_answer(
        question="How do applicants monitor injection pressure and flow rate?",
        evidence_items=evidence,
    )

    assert "Based on the retrieved permit-precedent evidence" in answer
    assert "[E1]" in answer
    assert "[E2]" in answer
    assert "mass flowmeter" in answer
    assert "injection pressure" in answer


def test_build_evidence_grounded_answer_handles_empty_evidence():
    from rag.answer_synthesis import build_evidence_grounded_answer

    answer = build_evidence_grounded_answer(
        question="What is required?",
        evidence_items=[],
    )

    assert "Insufficient context" in answer


def test_build_evidence_grounded_answer_handles_no_relevant_sentences():
    from rag.answer_synthesis import build_evidence_grounded_answer

    evidence = [
        make_evidence(
            "E1",
            Collection.PERMITS,
            "Administrative contact information is listed.",
        )
    ]

    answer = build_evidence_grounded_answer(
        question="fracture gradient geomechanics",
        evidence_items=evidence,
    )

    assert "did not contain enough directly relevant text" in answer