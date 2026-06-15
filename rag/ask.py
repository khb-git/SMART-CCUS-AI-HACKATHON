"""
End-to-end ask CLI for the Class VI review assistant.

This module connects:
    question
        -> diversified retrieval
        -> evidence packaging
        -> structured review answer
"""

from __future__ import annotations

import argparse

from rag.embeddings import DEFAULT_MODEL, Embeddings
from rag.evidence import package_evidence
from rag.retriever import Retriever
from rag.review_answer import build_template_answer, format_review_answer
from rag.vectorstore import VectorStore

from rag.query_intent import QueryIntent, classify_query_intent
from rag.rag_types import Collection
from rag.query_expansion import expand_query


def ask_question(
    question: str,
    persist_directory: str = "./chroma_data",
    model_name: str = DEFAULT_MODEL,
    section_id: str = "",
    k_reference: int = 3,
    k_permits: int = 5,
    fetch_k: int = 30,
    max_per_source: int = 1,
    intent: str = "auto",
    expand_retrieval_query: bool = True,
    use_reranking: bool = True,
):
    """Answer a review question using reference and permit evidence."""
    embeddings = Embeddings(model_name=model_name)
    store = VectorStore(persist_directory=persist_directory)
    retriever = Retriever(embeddings=embeddings, store=store)

    route = classify_query_intent(question)

    if intent != "auto":
        if intent == QueryIntent.REGULATORY_REQUIREMENT.value:
            route.collections = [Collection.REFERENCE]
            route.intent = QueryIntent.REGULATORY_REQUIREMENT
            route.reason = "User explicitly requested reference-only routing."
        elif intent == QueryIntent.PERMIT_PRECEDENT.value:
            route.collections = [Collection.PERMITS]
            route.intent = QueryIntent.PERMIT_PRECEDENT
            route.reason = "User explicitly requested permit-only routing."
        elif intent == QueryIntent.CROSS_CHECK.value:
            route.collections = [Collection.REFERENCE, Collection.PERMITS]
            route.intent = QueryIntent.CROSS_CHECK
            route.reason = "User explicitly requested cross-check routing."
        elif intent == QueryIntent.GENERAL_REVIEW.value:
            route.collections = [Collection.REFERENCE, Collection.PERMITS]
            route.intent = QueryIntent.GENERAL_REVIEW
            route.reason = "User explicitly requested general-review routing."
        else:
            raise ValueError(f"Unsupported intent: {intent}")

    reference_results = []
    permit_results = []

    retrieval_query = expand_query(
        question,
        enabled=expand_retrieval_query,
    )

    if route.uses_reference():
        reference_results = retriever.retrieve_reference_diversified(
            query_text=retrieval_query,
            section_id=section_id,
            k=k_reference,
            fetch_k=fetch_k,
            max_per_source=max_per_source,
            rerank_query=question,
            use_reranking=use_reranking,
        )

    if route.uses_permits():
        permit_results = retriever.retrieve_permits_diversified(
            query_text=retrieval_query,
            section_id=section_id,
            k=k_permits,
            fetch_k=fetch_k,
            max_per_source=max_per_source,
            rerank_query=question,
            use_reranking=use_reranking,
        )

    reference_evidence = package_evidence(
        reference_results,
        start_index=1,
    )

    permit_evidence = package_evidence(
        permit_results,
        start_index=len(reference_evidence) + 1,
    )

    print("Reference results:", len(reference_results))
    print("Permit results:", len(permit_results))

    evidence_items = reference_evidence + permit_evidence

    # Detect sections from retrieved evidence
    detected_sections = sorted(
        {
            str(item.get("schema_section_id"))
            for item in evidence_items
            if item.get("schema_section_id")
        }
    )

    answer = build_template_answer(
        question=question,
        evidence_items=evidence_items,
    )

    # Attach detected sections
    answer.detected_sections = detected_sections

    return answer



def parse_args():
    parser = argparse.ArgumentParser(
        description="Ask a Class VI permit review question using indexed evidence.",
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Review question to answer.",
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
        "--section-id",
        default="",
        help="Optional schema section filter, such as 8 for Testing and Monitoring.",
    )
    parser.add_argument(
        "--k-reference",
        type=int,
        default=3,
        help="Number of reference evidence items. Default: 3.",
    )
    parser.add_argument(
        "--k-permits",
        type=int,
        default=5,
        help="Number of permit precedent evidence items. Default: 5.",
    )
    parser.add_argument(
        "--fetch-k",
        type=int,
        default=30,
        help="Raw retrieval count before diversification. Default: 30.",
    )
    parser.add_argument(
        "--max-per-source",
        type=int,
        default=1,
        help="Maximum evidence items per source document. Default: 1.",
    )
    parser.add_argument(
        "--intent",
        default="auto",
        choices=[
            "auto",
            QueryIntent.REGULATORY_REQUIREMENT.value,
            QueryIntent.PERMIT_PRECEDENT.value,
            QueryIntent.CROSS_CHECK.value,
            QueryIntent.GENERAL_REVIEW.value,
        ],
        help="Retrieval intent. Default: auto.",
    )
    parser.add_argument(
        "--no-query-expansion",
        action="store_true",
        help="Disable rule-based query expansion during retrieval.",
    )
    parser.add_argument(
        "--no-reranking",
        action="store_true",
        help="Disable local reranking after vector retrieval.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    review_answer = ask_question(
        question=args.query,
        persist_directory=args.persist_directory,
        model_name=args.model_name,
        section_id=args.section_id,
        k_reference=args.k_reference,
        k_permits=args.k_permits,
        fetch_k=args.fetch_k,
        max_per_source=args.max_per_source,
        intent=args.intent,
        expand_retrieval_query=not args.no_query_expansion,
        use_reranking=not args.no_reranking,
    )

    print(format_review_answer(review_answer))

if __name__ == "__main__":
    main()



