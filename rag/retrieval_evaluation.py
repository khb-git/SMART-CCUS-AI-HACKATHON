"""
Retrieval quality evaluation for the Class VI review assistant.

This module provides a repeatable way to evaluate retrieval quality across
important review queries. It is not meant to prove correctness by itself; it
helps identify weak retrieval cases, low similarity scores, and missing
expected technical evidence.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from rag.embeddings import DEFAULT_MODEL
from rag.query_chroma import query_collection
from rag.types import Collection, RetrievalResult


DEFAULT_SCORE_THRESHOLD = 0.85


@dataclass
class RetrievalEvaluationCase:
    """One retrieval evaluation case."""

    case_id: str
    query: str
    collection: str
    section_id: str = ""
    expected_terms: list[str] = field(default_factory=list)
    expected_plan_types: list[str] = field(default_factory=list)
    min_top_score: float = DEFAULT_SCORE_THRESHOLD
    k: int = 5
    fetch_k: int = 30
    max_per_source: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable case data."""
        return {
            "case_id": self.case_id,
            "query": self.query,
            "collection": self.collection,
            "section_id": self.section_id,
            "expected_terms": self.expected_terms,
            "expected_plan_types": self.expected_plan_types,
            "min_top_score": self.min_top_score,
            "k": self.k,
            "fetch_k": self.fetch_k,
            "max_per_source": self.max_per_source,
        }


@dataclass
class RetrievalEvaluationResult:
    """Evaluation result for one retrieval case."""

    case_id: str
    query: str
    collection: str
    result_count: int
    top_score: float
    max_score: float
    min_top_score: float
    score_passed: bool
    expected_terms_found: list[str]
    expected_terms_missing: list[str]
    expected_plan_types_found: list[str]
    expected_plan_types_missing: list[str]
    failure_reasons: list[str]
    score_band: str
    passed: bool
    top_sources: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable result data."""
        return {
            "case_id": self.case_id,
            "query": self.query,
            "collection": self.collection,
            "result_count": self.result_count,
            "top_score": self.top_score,
            "max_score": self.max_score,
            "min_top_score": self.min_top_score,
            "score_passed": self.score_passed,
            "expected_terms_found": self.expected_terms_found,
            "expected_terms_missing": self.expected_terms_missing,
            "expected_plan_types_found": self.expected_plan_types_found,
            "expected_plan_types_missing": self.expected_plan_types_missing,
            "failure_reasons": self.failure_reasons,
            "score_band": self.score_band,
            "passed": self.passed,
            "top_sources": self.top_sources,
        }


@dataclass
class RetrievalEvaluationSummary:
    """Summary for a set of retrieval evaluation results."""

    total_cases: int
    passed_cases: int
    failed_cases: int
    score_passed_cases: int
    average_top_score: float
    weak_cases: list[str]
    results: list[RetrievalEvaluationResult]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable summary data."""
        return {
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "score_passed_cases": self.score_passed_cases,
            "average_top_score": self.average_top_score,
            "weak_cases": self.weak_cases,
            "results": [result.to_dict() for result in self.results],
        }


DEFAULT_RETRIEVAL_EVALUATION_CASES = [
    RetrievalEvaluationCase(
        case_id="permits_pressure_flow_monitoring",
        query="How do applicants monitor injection pressure and flow rate?",
        collection=Collection.PERMITS.value,
        section_id="8",
        expected_terms=[
            "injection pressure",
            "flow rate",
            "monitoring",
        ],
        expected_plan_types=["testing_monitoring"],
        min_top_score=0.85,
    ),
    RetrievalEvaluationCase(
        case_id="permits_annular_pressure_monitoring",
        query="How do applicants monitor annular pressure?",
        collection=Collection.PERMITS.value,
        section_id="8",
        expected_terms=[
            "annular pressure",
            "annulus pressure",
            "monitoring",
        ],
        expected_plan_types=["testing_monitoring"],
        min_top_score=0.85,
    ),
    RetrievalEvaluationCase(
        case_id="permits_plume_pressure_front_tracking",
        query="How do applicants track plume and pressure front movement?",
        collection=Collection.PERMITS.value,
        section_id="8",
        expected_terms=[
            "plume",
            "pressure front",
            "monitoring",
        ],
        expected_plan_types=["testing_monitoring"],
        min_top_score=0.85,
    ),
    RetrievalEvaluationCase(
        case_id="reference_testing_monitoring_requirements",
        query="What does Class VI require for testing and monitoring?",
        collection=Collection.REFERENCE.value,
        section_id="8",
        expected_terms=[
            "testing",
            "monitoring",
            "Class VI",
        ],
        expected_plan_types=[],
        min_top_score=0.85,
    ),
    RetrievalEvaluationCase(
        case_id="permits_pisc_requirements",
        query="How do applicants describe post-injection site care and site closure?",
        collection=Collection.PERMITS.value,
        section_id="10",
        expected_terms=[
            "post-injection site care",
            "site closure",
            "PISC",
        ],
        expected_plan_types=["pisc_site_closure"],
        min_top_score=0.85,
    ),
    RetrievalEvaluationCase(
        case_id="permits_financial_responsibility",
        query="How do applicants demonstrate financial responsibility?",
        collection=Collection.PERMITS.value,
        section_id="4",
        expected_terms=[
            "financial responsibility",
            "cost estimate",
            "financial assurance",
        ],
        expected_plan_types=["financial_responsibility"],
        min_top_score=0.85,
    ),
    RetrievalEvaluationCase(
        case_id="permits_well_construction",
        query="What should be included in a well construction plan?",
        collection=Collection.PERMITS.value,
        section_id="5",
        expected_terms=[
            "casing",
            "cement",
            "tubing",
            "packer",
        ],
        expected_plan_types=["well_construction"],
        min_top_score=0.85,
    ),
]


def normalize_text(value: str) -> str:
    """Normalize text for simple matching."""
    return " ".join(
        str(value or "")
        .lower()
        .replace("-", " ")
        .replace("_", " ")
        .replace("/", " ")
        .split()
    )


def collect_result_text(results: list[RetrievalResult]) -> str:
    """Collect retrieved text for evidence-term checks."""
    return "\n\n".join(result.chunk.text for result in results)


def find_terms_in_text(terms: list[str], text: str) -> list[str]:
    """Return expected terms found in text."""
    normalized_text = normalize_text(text)

    return [
        term
        for term in terms
        if normalize_text(term) in normalized_text
    ]


def find_plan_types_in_results(
    expected_plan_types: list[str],
    results: list[RetrievalResult],
) -> list[str]:
    """Return expected plan types found in result metadata."""
    found = set()

    for result in results:
        plan_type = getattr(result.chunk.metadata, "plan_type", "") or ""

        if plan_type in expected_plan_types:
            found.add(plan_type)

    return sorted(found)

def classify_score_band(score: float) -> str:
    """Classify retrieval score into a readable diagnostic band."""
    if score >= 0.90:
        return "excellent"
    if score >= 0.85:
        return "strong"
    if score >= 0.70:
        return "moderate"
    if score > 0:
        return "weak"

    return "no_results"


def get_failure_reasons(
    result_count: int,
    score_passed: bool,
    expected_terms_missing: list[str],
    expected_plan_types_missing: list[str],
) -> list[str]:
    """Return high-level failure reasons for one retrieval case."""
    reasons = []

    if result_count == 0:
        reasons.append("no_results")

    if not score_passed:
        reasons.append("score_below_threshold")

    if expected_terms_missing:
        reasons.append("expected_terms_missing")

    if expected_plan_types_missing:
        reasons.append("expected_plan_types_missing")

    return reasons

def summarize_top_sources(
    results: list[RetrievalResult],
    max_sources: int = 5,
) -> list[dict[str, Any]]:
    """Summarize top sources returned for a case."""
    sources = []

    for result in results[:max_sources]:
        metadata = result.chunk.metadata

        sources.append(
            {
                "score": result.score,
                "source_document": getattr(metadata, "source_document", ""),
                "page_number": getattr(metadata, "page_number", 0),
                "chunk_index": getattr(metadata, "chunk_index", 0),
                "plan_type": getattr(metadata, "plan_type", ""),
                "content_type": getattr(metadata, "content_type", ""),
                "schema_section_id": getattr(metadata, "schema_section_id", ""),
                "schema_section_title": getattr(
                    metadata,
                    "schema_section_title",
                    "",
                ),
            }
        )

    return sources


def evaluate_retrieval_case(
    case: RetrievalEvaluationCase,
    persist_directory: str = "./chroma_data",
    model_name: str = DEFAULT_MODEL,
    expand_retrieval_query: bool = True,
    use_reranking: bool = True,
    diversified: bool = True,
    retrieval_function: Callable[..., list[RetrievalResult]] = query_collection,
) -> RetrievalEvaluationResult:
    """Evaluate one retrieval case."""
    results = retrieval_function(
        query=case.query,
        collection=Collection(case.collection),
        persist_directory=persist_directory,
        model_name=model_name,
        k=case.k,
        section_id=case.section_id,
        diversified=diversified,
        fetch_k=case.fetch_k,
        max_per_source=case.max_per_source,
        expand_retrieval_query=expand_retrieval_query,
        use_reranking=use_reranking,
    )

    top_score = results[0].score if results else 0.0
    max_score = max((result.score for result in results), default=0.0)
    score_passed = max_score >= case.min_top_score
    score_band = classify_score_band(max_score)

    result_text = collect_result_text(results)

    expected_terms_found = find_terms_in_text(
        case.expected_terms,
        result_text,
    )
    expected_terms_missing = [
        term for term in case.expected_terms if term not in expected_terms_found
    ]

    expected_plan_types_found = find_plan_types_in_results(
        case.expected_plan_types,
        results,
    )
    expected_plan_types_missing = [
        plan_type
        for plan_type in case.expected_plan_types
        if plan_type not in expected_plan_types_found
    ]

    failure_reasons = get_failure_reasons(
        result_count=len(results),
        score_passed=score_passed,
        expected_terms_missing=expected_terms_missing,
        expected_plan_types_missing=expected_plan_types_missing,
    )

    passed = bool(results) and score_passed

    if case.expected_terms:
        passed = passed and not expected_terms_missing

    if case.expected_plan_types:
        passed = passed and not expected_plan_types_missing

    return RetrievalEvaluationResult(
        case_id=case.case_id,
        query=case.query,
        collection=case.collection,
        result_count=len(results),
        top_score=top_score,
        max_score=max_score,
        min_top_score=case.min_top_score,
        score_passed=score_passed,
        expected_terms_found=expected_terms_found,
        expected_terms_missing=expected_terms_missing,
        expected_plan_types_found=expected_plan_types_found,
        expected_plan_types_missing=expected_plan_types_missing,
        failure_reasons=failure_reasons,
        score_band=score_band,
        passed=passed,
        top_sources=summarize_top_sources(results),
    )


def evaluate_retrieval_cases(
    cases: list[RetrievalEvaluationCase],
    persist_directory: str = "./chroma_data",
    model_name: str = DEFAULT_MODEL,
    expand_retrieval_query: bool = True,
    use_reranking: bool = True,
    diversified: bool = True,
    retrieval_function: Callable[..., list[RetrievalResult]] = query_collection,
) -> RetrievalEvaluationSummary:
    """Evaluate a list of retrieval cases."""
    results = [
        evaluate_retrieval_case(
            case=case,
            persist_directory=persist_directory,
            model_name=model_name,
            expand_retrieval_query=expand_retrieval_query,
            use_reranking=use_reranking,
            diversified=diversified,
            retrieval_function=retrieval_function,
        )
        for case in cases
    ]

    total_cases = len(results)
    passed_cases = sum(1 for result in results if result.passed)
    score_passed_cases = sum(1 for result in results if result.score_passed)
    failed_cases = total_cases - passed_cases

    average_top_score = (
        sum(result.top_score for result in results) / total_cases
        if total_cases
        else 0.0
    )

    weak_cases = [
        result.case_id
        for result in results
        if not result.passed
    ]

    return RetrievalEvaluationSummary(
        total_cases=total_cases,
        passed_cases=passed_cases,
        failed_cases=failed_cases,
        score_passed_cases=score_passed_cases,
        average_top_score=average_top_score,
        weak_cases=weak_cases,
        results=results,
    )


def print_evaluation_summary(summary: RetrievalEvaluationSummary) -> None:
    """Print a readable evaluation summary."""
    print("Retrieval Quality Evaluation")
    print("=" * 80)
    print(f"Total cases: {summary.total_cases}")
    print(f"Passed cases: {summary.passed_cases}")
    print(f"Failed cases: {summary.failed_cases}")
    print(f"Score threshold passed: {summary.score_passed_cases}")
    print(f"Average top score: {summary.average_top_score:.4f}")
    print()

    for result in summary.results:
        status = "PASS" if result.passed else "FAIL"

        print(f"[{status}] {result.case_id}")
        print(f"Query: {result.query}")
        print(f"Collection: {result.collection}")
        print(
            f"Ranked top score: {result.top_score:.4f} | "
            f"Max returned score: {result.max_score:.4f} / {result.min_top_score:.4f}"
        )
        print(f"Score band: {result.score_band}")
        print(f"Failure reasons: {result.failure_reasons}")
        print(f"Expected terms found: {result.expected_terms_found}")
        print(f"Expected terms missing: {result.expected_terms_missing}")
        print(f"Expected plan types found: {result.expected_plan_types_found}")
        print(f"Expected plan types missing: {result.expected_plan_types_missing}")
        print("Top sources:")

        for source in result.top_sources:
            print(
                "  "
                f"{source['score']:.4f} | "
                f"{source['source_document']} | "
                f"page {source['page_number']} | "
                f"plan_type={source['plan_type']} | "
                f"section={source['schema_section_id']}"
            )

        print("-" * 80)


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate retrieval quality across regression queries.",
    )
    parser.add_argument(
        "--persist-directory",
        default="./chroma_data",
        help="Chroma persistence directory. Default: ./chroma_data",
    )
    parser.add_argument(
        "--model-name",
        default=DEFAULT_MODEL,
        help=f"Embedding model name. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--output-json",
        default="",
        help="Optional path to write evaluation JSON.",
    )
    parser.add_argument(
        "--no-query-expansion",
        action="store_true",
        help="Disable query expansion during evaluation.",
    )
    parser.add_argument(
        "--no-reranking",
        action="store_true",
        help="Disable reranking during evaluation.",
    )
    parser.add_argument(
        "--no-diversified",
        action="store_true",
        help="Disable diversified retrieval during evaluation.",
    )

    return parser.parse_args()


def main():
    """Run retrieval evaluation CLI."""
    args = parse_args()

    summary = evaluate_retrieval_cases(
        cases=DEFAULT_RETRIEVAL_EVALUATION_CASES,
        persist_directory=args.persist_directory,
        model_name=args.model_name,
        expand_retrieval_query=not args.no_query_expansion,
        use_reranking=not args.no_reranking,
        diversified=not args.no_diversified,
    )

    print_evaluation_summary(summary)

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(summary.to_dict(), indent=2),
            encoding="utf-8",
        )
        print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()