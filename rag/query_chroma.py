"""
Query an indexed Chroma collection.

Example:
    python -m rag.query_chroma ^
        --query "What does Class VI require for testing and monitoring?" ^
        --collection reference ^
        --persist-directory chroma_data ^
        --k 5
"""

from __future__ import annotations

import argparse

from rag.embeddings import DEFAULT_MODEL, Embeddings
from rag.retriever import Retriever
from rag.types import Collection
from rag.vectorstore import VectorStore


def format_result(result, index: int) -> str:
    """Format one retrieval result for CLI display."""
    metadata = result.chunk.metadata

    preview = result.chunk.text.replace("\n", " ").strip()
    if len(preview) > 500:
        preview = preview[:500] + "..."

    lines = [
        f"Result {index}",
        f"Score: {result.score:.4f}",
        f"Collection: {result.collection.value}",
        f"Source document: {metadata.source_document}",
        f"Page: {metadata.page_number}",
        f"Chunk index: {metadata.chunk_index}",
        f"Content type: {metadata.content_type}",
        f"Plan type: {metadata.plan_type}",
        f"Schema section: {metadata.schema_section_id} {metadata.schema_section_title}".strip(),
        f"Online link: {metadata.online_link}",
        f"Source page: {metadata.source_page}",
        "",
        preview,
        "-" * 80,
    ]

    return "\n".join(lines)


def query_collection(
    query: str,
    collection: Collection,
    persist_directory: str = "./chroma_data",
    model_name: str = DEFAULT_MODEL,
    k: int = 5,
    section_id: str = "",
    diversified: bool = False,
    fetch_k: int = 30,
    max_per_source: int = 1,
):
    """Query one Chroma collection using the existing Retriever."""
    embeddings = Embeddings(model_name=model_name)
    store = VectorStore(persist_directory=persist_directory)
    retriever = Retriever(embeddings=embeddings, store=store)

    if collection == Collection.REFERENCE:
        if diversified:
            return retriever.retrieve_reference_diversified(
                query,
                section_id=section_id,
                k=k,
                fetch_k=fetch_k,
                max_per_source=max_per_source,
            )
        return retriever.retrieve_reference(query, section_id=section_id, k=k)

    if collection == Collection.PERMITS:
        if diversified:
            return retriever.retrieve_permits_diversified(
                query,
                section_id=section_id,
                k=k,
                fetch_k=fetch_k,
                max_per_source=max_per_source,
            )
        return retriever.retrieve_permits(query, section_id=section_id, k=k)

    raise ValueError(f"Unsupported collection: {collection}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a semantic retrieval smoke test against Chroma.",
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Question or search phrase to retrieve evidence for.",
    )
    parser.add_argument(
        "--collection",
        required=True,
        choices=[collection.value for collection in Collection],
        help="Collection to query: reference or permits.",
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
        "--k",
        type=int,
        default=5,
        help="Number of retrieval results. Default: 5.",
    )
    parser.add_argument(
        "--section-id",
        default="",
        help="Optional metadata filter for schema/section id, such as 8.",
    )
    parser.add_argument(
        "--diversified",
        action="store_true",
        help="Diversify results by source document.",
    )
    parser.add_argument(
        "--fetch-k",
        type=int,
        default=30,
        help="Number of raw Chroma results to fetch before diversification. Default: 30.",
    )
    parser.add_argument(
        "--max-per-source",
        type=int,
        default=1,
        help="Maximum number of final results from the same source document. Default: 1.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    collection = Collection(args.collection)

    results = query_collection(
        query=args.query,
        collection=collection,
        persist_directory=args.persist_directory,
        model_name=args.model_name,
        k=args.k,
        section_id=args.section_id,
        diversified=args.diversified,
        fetch_k=args.fetch_k,
        max_per_source=args.max_per_source,
    )

    print(f"Query: {args.query}")
    print(f"Collection: {collection.value}")
    print(f"Diversified: {args.diversified}")
    print(f"Results: {len(results)}")
    print("=" * 80)

    for i, result in enumerate(results, start=1):
        print(format_result(result, i))


if __name__ == "__main__":
    main()