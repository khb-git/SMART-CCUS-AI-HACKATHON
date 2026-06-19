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

from rag.generator import Generator

generator = Generator(model_name="llama3")


def build_llm_prompt(question, evidence_items):
    context = "\n\n".join(
        f"[{i+1}] Section {item.schema_section_id}:\n{item.excerpt}"
        for i, item in enumerate(evidence_items)
    )

    return f"""
You are an expert EPA Class VI carbon storage permit reviewer assistant.

Your task is to answer question from reviewers to help them review permits. 

Rules:
- Summarize technical aspects using reference and permits evidence.
- Give specific examples using previous permit applications evidence and information.
- Only use the provided evidence
- Do NOT hallucinate
- If evidence is missing, say: "Insufficient context"


Question:
{question}

Evidence:
{context}

Output format:
1. Direct answer (technical)
2. Cite evidence like [1], [2]
3. If incomplete → clearly state what is missing


Answer:
"""


def generate_interpretation(answer_text):
    prompt = f"""
Interpret the following answer as a regulator reviewing a Class VI permit:

{answer_text}

Explain:
- What is sufficient
- What is missing or unclear
"""

    try:
        return generator.generate(prompt)
    except Exception:
        return "Interpretation could not be generated."


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
    use_llm: bool = True,
):
    """Answer a review question using reference and permit evidence."""

    embeddings = Embeddings(model_name=model_name)
    store = VectorStore(persist_directory=persist_directory)
    retriever = Retriever(embeddings=embeddings, store=store)

    route = classify_query_intent(question)

    if intent != "auto":
        if intent == QueryIntent.REGULATORY_REQUIREMENT.value:
            route.collections = [Collection.REFERENCE]
        elif intent == QueryIntent.PERMIT_PRECEDENT.value:
            route.collections = [Collection.PERMITS]
        elif intent in (
            QueryIntent.CROSS_CHECK.value,
            QueryIntent.GENERAL_REVIEW.value,
        ):
            route.collections = [Collection.REFERENCE, Collection.PERMITS]
        else:
            raise ValueError(f"Unsupported intent: {intent}")

    # Retrieval
    reference_results = []
    permit_results = []

    retrieval_query = expand_query(question, enabled=expand_retrieval_query)

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

    # Evidence packaging
    reference_evidence = package_evidence(reference_results, start_index=1)
    permit_evidence = package_evidence(
        permit_results,
        start_index=len(reference_evidence) + 1,
    )

    evidence_items = reference_evidence + permit_evidence

    print("Reference results:", len(reference_results))
    print("Permit results:", len(permit_results))

    # Detect sections
    detected_sections = sorted(
        {
            str(item.schema_section_id)
            for item in evidence_items
            if item.schema_section_id
        }
    )

    # Base template answer (fallback-safe)
    answer = build_template_answer(
        question=question,
        evidence_items=evidence_items,
    )

    # LLM override (optional)
    if use_llm and evidence_items:
        prompt = build_llm_prompt(question, evidence_items)
        try:
            answer.answer = generator.generate(prompt)
        except Exception as e:
            print(f"LLM error: {e}")
    elif not evidence_items:
        answer.answer = "Insufficient context to determine based on retrieved evidence."

    # Add interpretation (optional and safe)
    if use_llm and answer.answer:
        answer.reviewer_interpretation = generate_interpretation(
            answer.answer
        )

    # Attach detected sections
    answer.detected_sections = detected_sections

    return answer


def parse_args():
    parser = argparse.ArgumentParser(
        description="Ask a Class VI permit review question using indexed evidence.",
    )

    parser.add_argument("--query", required=True)
    parser.add_argument("--persist-directory", default="./chroma_data")
    parser.add_argument("--model-name", default=DEFAULT_MODEL)
    parser.add_argument("--section-id", default="")
    parser.add_argument("--k-reference", type=int, default=3)
    parser.add_argument("--k-permits", type=int, default=5)
    parser.add_argument("--fetch-k", type=int, default=30)
    parser.add_argument("--max-per-source", type=int, default=1)
    parser.add_argument("--intent", default="auto")
    parser.add_argument("--no-query-expansion", action="store_true")
    parser.add_argument("--no-reranking", action="store_true")

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
