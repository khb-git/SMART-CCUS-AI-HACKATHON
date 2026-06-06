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

REFERENCE_KEYWORDS = [
    "implementation manual",
    "guidance",
    "class vi guidance",
    "final class vi",
    "cfr",
    "40 cfr",
    "regulation",
    "regulatory",
    "statutory",
    "application outline",
    "completeness tool",
    "template",
    "pamphlet",
    "report to congress",
    "rules and tools",
    "crosswalk",
    "compendium",
    "deep saline formation",
]

PERMIT_KEYWORDS = [
    "adm",
    "hgcs",
    "lorain",
    "marquis",
    "wabash",
    "one earth",
    "one carbon",
    "project narrative",
    "aor",
    "corrective action",
    "well construction",
    "testing and monitoring plan",
    "injection well plugging",
    "pisc",
    "site closure",
    "emergency and remedial",
    "errp",
    "pre-operational testing",
    "financial responsibility",
    "cost estimates",
]


def normalize_for_routing(value):
    """Normalize text for lightweight collection routing."""
    return (
        str(value or "")
        .lower()
        .replace("_", " ")
        .replace("-", " ")
        .replace("+", " ")
        .replace("%20", " ")
    )


def infer_collection_target(document_attr, chunk_attr=None):
    """Infer whether a chunk belongs in reference or permits.

    Long-term, this should come from manifest-level metadata such as
    collection_target. For now, this provides a practical fallback using
    source metadata, filenames, URLs, and summaries.
    """
    chunk_attr = chunk_attr or {}

    explicit = (
        chunk_attr.get("collection_target")
        or document_attr.get("collection_target")
        or document_attr.get("collection")
        or chunk_attr.get("collection")
    )

    if explicit:
        explicit = normalize_for_routing(explicit)
        if explicit in {"reference", "permits"}:
            return Collection(explicit)

    combined = " ".join(
        [
            normalize_for_routing(document_attr.get("datasource_name", "")),
            normalize_for_routing(document_attr.get("online_link", "")),
            normalize_for_routing(document_attr.get("source_page", "")),
            normalize_for_routing(document_attr.get("summary", "")),
            normalize_for_routing(chunk_attr.get("datasource_name", "")),
            normalize_for_routing(chunk_attr.get("online_link", "")),
            normalize_for_routing(chunk_attr.get("source_page", "")),
            normalize_for_routing(chunk_attr.get("summary", "")),
        ]
    )

    strong_reference_signals = [
        "template",
        "permit application templates",
        "final class vi guidance",
        "guidance documents",
        "implementation manual",
        "completeness tool",
        "application completeness tool",
        "application outline",
        "pamphlet",
        "report to congress",
        "regulatory",
        "statutory",
        "rules and tools",
        "crosswalk",
        "compendium",
    ]

    if any(signal in combined for signal in strong_reference_signals):
        return Collection.REFERENCE

    reference_hits = sum(1 for keyword in REFERENCE_KEYWORDS if keyword in combined)
    permit_hits = sum(1 for keyword in PERMIT_KEYWORDS if keyword in combined)

    if reference_hits > permit_hits:
        return Collection.REFERENCE

    if permit_hits > reference_hits:
        return Collection.PERMITS

    # Conservative fallback: permit applications are the higher-risk source
    # to accidentally mix into reference guidance.
    return Collection.PERMITS

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
        section_heading=chunk_attr.get("section_heading", ""),
        local_section_title=chunk_attr.get("local_section_title", ""),
        detected_heading_on_page=chunk_attr.get("detected_heading_on_page", ""),
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

def load_chunks_from_chunked_dir_auto(
    chunked_dir,
    project_name: str = "",
) -> dict[Collection, list[Chunk]]:
    """Load chunks and route each one to reference or permits automatically."""
    chunked_dir = Path(chunked_dir)

    if not chunked_dir.exists():
        raise FileNotFoundError(f"Chunked directory not found: {chunked_dir}")

    routed = {
        Collection.REFERENCE: [],
        Collection.PERMITS: [],
    }

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
            collection = infer_collection_target(document_attr, chunk_attr)

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

            routed[collection].append(
                Chunk(
                    text=text,
                    metadata=metadata,
                    chunk_id=chunk_id,
                )
            )

    return routed

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

def index_chunked_directory_auto(
    chunked_dir,
    persist_directory="./chroma_data",
    model_name=DEFAULT_MODEL,
    batch_size: int = 64,
    project_name: str = "",
) -> dict[Collection, int]:
    """Auto-route chunked ingestion output into reference/permits collections."""
    routed_chunks = load_chunks_from_chunked_dir_auto(
        chunked_dir=chunked_dir,
        project_name=project_name,
    )

    embeddings = Embeddings(model_name=model_name)
    store = VectorStore(persist_directory=persist_directory)

    counts = {}

    for collection, chunks in routed_chunks.items():
        counts[collection] = index_chunks(
            chunks=chunks,
            collection=collection,
            embeddings=embeddings,
            store=store,
            batch_size=batch_size,
        )

    return counts

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
        choices=[collection.value for collection in Collection] + ["auto"],
        help="Vector collection to index into: permits, reference, or auto.",
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

    if args.collection == "auto":
        counts = index_chunked_directory_auto(
            chunked_dir=args.chunked_dir,
            persist_directory=args.persist_directory,
            model_name=args.model_name,
            batch_size=args.batch_size,
            project_name=args.project_name,
        )

        print("Indexed chunks using automatic collection routing:")
        for collection, count in counts.items():
            print(f"- {collection.value}: {count}")
        return

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