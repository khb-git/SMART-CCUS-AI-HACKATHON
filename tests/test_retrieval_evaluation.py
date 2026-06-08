import pytest

from rag.types import Chunk, ChunkMetadata, Collection, DocumentType, RetrievalResult


def make_result(
    text: str,
    score: float,
    source_document: str = "source.pdf",
    plan_type: str = "testing_monitoring",
    page_number: int = 1,
):
    metadata = ChunkMetadata(
        source_document=source_document,
        document_type=DocumentType.PERMIT_APPLICATION,
        page_number=page_number,
        chunk_index=0,
        plan_type=plan_type,
        content_type="text",
        schema_section_id="8",
        schema_section_title="Testing and Monitoring Plan",
    )

    chunk = Chunk(
        text=text,
        metadata=metadata,
        chunk_id=f"{source_document}_{page_number}",
    )

    return RetrievalResult(
        chunk=chunk,
        score=score,
        collection=Collection.PERMITS,
    )


def test_find_terms_in_text_matches_normalized_terms():
    from rag.retrieval_evaluation import find_terms_in_text

    text = "The plan describes injection-pressure monitoring and flow rate tracking."

    found = find_terms_in_text(
        ["injection pressure", "flow rate", "annular pressure"],
        text,
    )

    assert found == ["injection pressure", "flow rate"]


def test_evaluate_retrieval_case_passes_when_score_terms_and_plan_type_match():
    from rag.retrieval_evaluation import (
        RetrievalEvaluationCase,
        evaluate_retrieval_case,
    )

    case = RetrievalEvaluationCase(
        case_id="test_case",
        query="How do applicants monitor injection pressure and flow rate?",
        collection="permits",
        section_id="8",
        expected_terms=["injection pressure", "flow rate"],
        expected_plan_types=["testing_monitoring"],
        min_top_score=0.85,
    )

    def fake_retrieval_function(**kwargs):
        return [
            make_result(
                text="Injection pressure and flow rate are monitored continuously.",
                score=0.91,
                plan_type="testing_monitoring",
            )
        ]

    result = evaluate_retrieval_case(
        case,
        retrieval_function=fake_retrieval_function,
    )

    assert result.passed is True
    assert result.score_passed is True
    assert result.top_score == 0.91
    assert result.max_score == 0.91
    assert result.expected_terms_missing == []
    assert result.expected_plan_types_missing == []


def test_evaluate_retrieval_case_fails_when_score_is_low():
    from rag.retrieval_evaluation import (
        RetrievalEvaluationCase,
        evaluate_retrieval_case,
    )

    case = RetrievalEvaluationCase(
        case_id="low_score_case",
        query="How do applicants monitor injection pressure?",
        collection="permits",
        expected_terms=["injection pressure"],
        expected_plan_types=["testing_monitoring"],
        min_top_score=0.85,
    )

    def fake_retrieval_function(**kwargs):
        return [
            make_result(
                text="Injection pressure is monitored.",
                score=0.70,
                plan_type="testing_monitoring",
            )
        ]

    result = evaluate_retrieval_case(
        case,
        retrieval_function=fake_retrieval_function,
    )

    assert result.passed is False
    assert result.score_passed is False
    assert result.expected_terms_missing == []


def test_evaluate_retrieval_case_fails_when_expected_terms_are_missing():
    from rag.retrieval_evaluation import (
        RetrievalEvaluationCase,
        evaluate_retrieval_case,
    )

    case = RetrievalEvaluationCase(
        case_id="missing_terms_case",
        query="How do applicants monitor annular pressure?",
        collection="permits",
        expected_terms=["annular pressure"],
        expected_plan_types=["testing_monitoring"],
        min_top_score=0.85,
    )

    def fake_retrieval_function(**kwargs):
        return [
            make_result(
                text="Injection pressure is monitored.",
                score=0.90,
                plan_type="testing_monitoring",
            )
        ]

    result = evaluate_retrieval_case(
        case,
        retrieval_function=fake_retrieval_function,
    )

    assert result.passed is False
    assert result.score_passed is True
    assert result.expected_terms_missing == ["annular pressure"]


def test_evaluate_retrieval_cases_builds_summary():
    from rag.retrieval_evaluation import (
        RetrievalEvaluationCase,
        evaluate_retrieval_cases,
    )

    cases = [
        RetrievalEvaluationCase(
            case_id="pass_case",
            query="How do applicants monitor flow rate?",
            collection="permits",
            expected_terms=["flow rate"],
            expected_plan_types=["testing_monitoring"],
            min_top_score=0.85,
        ),
        RetrievalEvaluationCase(
            case_id="fail_case",
            query="How do applicants monitor annular pressure?",
            collection="permits",
            expected_terms=["annular pressure"],
            expected_plan_types=["testing_monitoring"],
            min_top_score=0.85,
        ),
    ]

    def fake_retrieval_function(query, **kwargs):
        if "flow rate" in query:
            return [
                make_result(
                    text="Flow rate is monitored.",
                    score=0.90,
                    plan_type="testing_monitoring",
                )
            ]

        return [
            make_result(
                text="Injection pressure is monitored.",
                score=0.80,
                plan_type="testing_monitoring",
            )
        ]

    summary = evaluate_retrieval_cases(
        cases,
        retrieval_function=fake_retrieval_function,
    )

    assert summary.total_cases == 2
    assert summary.passed_cases == 1
    assert summary.failed_cases == 1
    assert summary.score_passed_cases == 1
    assert summary.weak_cases == ["fail_case"]
    assert summary.average_top_score == pytest.approx(0.85)


def test_default_retrieval_evaluation_cases_have_thresholds():
    from rag.retrieval_evaluation import DEFAULT_RETRIEVAL_EVALUATION_CASES

    assert DEFAULT_RETRIEVAL_EVALUATION_CASES
    assert all(case.min_top_score >= 0.85 for case in DEFAULT_RETRIEVAL_EVALUATION_CASES)
    assert all(case.query for case in DEFAULT_RETRIEVAL_EVALUATION_CASES)
    assert all(case.collection in {"reference", "permits"} for case in DEFAULT_RETRIEVAL_EVALUATION_CASES)

def test_evaluate_retrieval_case_uses_max_score_for_score_threshold():
    from rag.retrieval_evaluation import (
        RetrievalEvaluationCase,
        evaluate_retrieval_case,
    )

    case = RetrievalEvaluationCase(
        case_id="reranked_case",
        query="How do applicants demonstrate financial responsibility?",
        collection="permits",
        expected_terms=["financial responsibility"],
        expected_plan_types=["financial_responsibility"],
        min_top_score=0.85,
    )

    def fake_retrieval_function(**kwargs):
        return [
            make_result(
                text="Financial responsibility is demonstrated through cost estimates.",
                score=0.70,
                plan_type="financial_responsibility",
            ),
            make_result(
                text="Financial responsibility and financial assurance are documented.",
                score=0.90,
                plan_type="financial_responsibility",
            ),
        ]

    result = evaluate_retrieval_case(
        case,
        retrieval_function=fake_retrieval_function,
    )

    assert result.top_score == 0.70
    assert result.max_score == 0.90
    assert result.score_passed is True