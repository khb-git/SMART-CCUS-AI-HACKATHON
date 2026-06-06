"""
Index chunked ingestion output into the vector store.

This module bridges:

    data/chunked/
        document_folder/
            attribute.json
            0/content.txt
            0/attribute.json
            ...

into:

    rag.types.Chunk
        ↓
    Embeddings
        ↓
    VectorStore / Chroma
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from rag.embeddings import DEFAULT_MODEL, Embeddings
from rag.types import Chunk, ChunkMetadata, Collection, DocumentType
from rag.vectorstore import VectorStore


def load_json(path: Path) -> dict:
    """Load a JSON file as a dictionary."""
    return json.loads(path.read_text(encoding="utf-8"))


def document_type_for_collection(collection: Collection) -> DocumentType:
    """Choose a default DocumentType based on the vector collection."""
    if collection == Collection.REFERENCE:
        return DocumentType.EPA_GUIDANCE
    return DocumentType.PERMIT_APPLICATION


def sorted_chunk_dirs(document_dir: Path):
    """Return chunk subdirectories sorted numerically when possible."""
    chunk_dirs = [
        child for child in document_dir.iterdir()
        if child.is_dir()
    ]

    def sort_key(path: Path):
        try:
            return int(path.name)
        except ValueError:
            return path.name

    return sorted(chunk_dirs, key=sort_key)


def build_chunk_metadata(
    document_attr: dict,
    chunk_attr: dict,
    collection: Collection,
    project_name: str = "",
) -> ChunkMetadata:
    """Build RAG ChunkMetadata from ingestion attribute files."""
    datasource_name = (
        chunk_attr.get("datasource_name")
        or document_attr.get("datasource_name")
        or ""
    )

    schema_section_id = (
        chunk_attr.get("schema_section_id")
        or document_attr.get("schema_section_id")
        or ""
    )

    return ChunkMetadata(
        source_document=datasource_name,
        document_type=document_type_for_collection(collection),
        project_name=project_name,
        section_id=schema_section_id,
        subsection_id=chunk_attr.get("subsection_id", ""),
        page_number=int(chunk_attr.get("page", 0) or 0),
        chunk_index=int(chunk_attr.get("chunk_index", 0) or 0),
        cfr_citation=chunk_attr.get("cfr_citation", ""),
        plan_type=chunk_attr.get("plan_type", document_attr.get("plan_type", "")),
        schema_section_id=schema_section_id,
        schema_section_title=chunk_attr.get(
            "schema_section_title",
            document_attr.get("schema_section_title", ""),
        ),
        content_type=chunk_attr.get("content_type", "text"),
        table_index=int(chunk_attr.get("table_index", -1) or -1),
        sheet_name=chunk_attr.get("sheet_name", ""),
        row_start=int(chunk_attr.get("row_start", -1) or -1),
        row_end=int(chunk_attr.get("row_end", -1) or -1),
        local_path=chunk_attr.get("local_path", document_attr.get("local_path", "")),
        online_link=chunk_attr.get("online_link", document_attr.get("online_link", "")),
        source_page=chunk_attr.get("source_page", document_attr.get("source_page", "")),
        summary=chunk_attr.get("summary", document_attr.get("summary", "")),
    )


def load_chunks_from_chunked_dir(
    chunked_dir,
    collection,
    project_name: str = "",
) -> list[Chunk]:
    """Load all content.txt/attribute.json pairs from a chunked output directory."""
    chunked_dir = Path(chunked_dir)
    collection = Collection(collection)

    if not chunked_dir.exists():
        raise FileNotFoundError(f"Chunked directory not found: {chunked_dir}")

    chunks: list[Chunk] = []

    for document_dir in sorted(p for p in chunked_dir.iterdir() if p.is_dir()):
        document_attr_path = document_dir / "attribute.json"

        if not document_attr_path.exists():
            continue

        document_attr = load_json(document_attr_path)

        for chunk_dir in sorted_chunk_dirs(document_dir):
            content_path = chunk_dir / "content.txt"
            chunk_attr_path = chunk_dir / "attribute.json"

            if not content_path.exists() or not chunk_attr_path.exists():
                continue

            text = content_path.read_text(encoding="utf-8").strip()
            if not text:
                continue

            chunk_attr = load_json(chunk_attr_path)
            metadata = build_chunk_metadata(
                document_attr=document_attr,
                chunk_attr=chunk_attr,
                collection=collection,
                project_name=project_name,
            )

            chunk_id = (
                chunk_attr.get("chunk_id")
                or f"{document_dir.name}:{metadata.chunk_index}"
            )

            chunks.append(
                Chunk(
                    text=text,
                    metadata=metadata,
                    chunk_id=chunk_id,
                )
            )

    return chunks


def batched(items, batch_size: int):
    """Yield batches from a list."""
    for start in range(0, len(items), batch_size):
        yield items[start:start + batch_size]


def index_chunks(
    chunks: list[Chunk],
    collection,
    embeddings: Embeddings,
    store: VectorStore,
    batch_size: int = 64,
) -> int:
    """Embed and store chunks in batches."""
    collection = Collection(collection)

    total = 0

    for batch in batched(chunks, batch_size):
        texts = [chunk.text for chunk in batch]
        vectors = embeddings.encode(texts)
        total += store.add(collection, batch, vectors)

    return total


def index_chunked_directory(
    chunked_dir,
    collection,
    persist_directory="./chroma_data",
    model_name=DEFAULT_MODEL,
    batch_size: int = 64,
    project_name: str = "",
) -> int:
    """Load chunked ingestion output, embed it, and store it in Chroma."""
    collection = Collection(collection)

    chunks = load_chunks_from_chunked_dir(
        chunked_dir=chunked_dir,
        collection=collection,
        project_name=project_name,
    )

    embeddings = Embeddings(model_name=model_name)
    store = VectorStore(persist_directory=persist_directory)

    return index_chunks(
        chunks=chunks,
        collection=collection,
        embeddings=embeddings,
        store=store,
        batch_size=batch_size,
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Index chunked Class VI ingestion output into Chroma.",
    )
    parser.add_argument(
        "--chunked-dir",
        required=True,
        type=Path,
        help="Path to data/chunked or another chunked ingestion output directory.",
    )
    parser.add_argument(
        "--collection",
        required=True,
        choices=[collection.value for collection in Collection],
        help="Vector collection to index into: permits or reference.",
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
        "--batch-size",
        type=int,
        default=64,
        help="Number of chunks to embed/store per batch. Default: 64.",
    )
    parser.add_argument(
        "--project-name",
        default="",
        help="Optional project name metadata for permit chunks.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    count = index_chunked_directory(
        chunked_dir=args.chunked_dir,
        collection=args.collection,
        persist_directory=args.persist_directory,
        model_name=args.model_name,
        batch_size=args.batch_size,
        project_name=args.project_name,
    )

    print(f"Indexed {count} chunks into collection '{args.collection}'")


if __name__ == "__main__":
    main()