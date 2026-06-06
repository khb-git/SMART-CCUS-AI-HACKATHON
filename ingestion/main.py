import argparse
import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.manifest import load_manifest

from dataclasses import dataclass

load_dotenv()

# Environment variables
source_dir = os.getenv("PATH_TO_RAW_DATA_DIR")
ingestion_folder = os.getenv("PATH_TO_CHUNKED_DATA_DIR")
manifest_path = os.getenv("PATH_TO_MANIFEST")

# Constant for EPA source
EPA_LINK = "https://www.epa.gov/uic/final-class-vi-guidance-documents"

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def build_splitter(chunk_size=1000, chunk_overlap=100):
    """Create the LangChain text splitter used by ingestion."""
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
    )


def write_chunks_for_document(file_path, chunks, output_root, metadata=None):
    """Write one document's chunks into the existing folder structure.

    Output shape:
        output_root/
            document_stem/
                attribute.json
                0/content.txt
                0/attribute.json
                1/content.txt
                1/attribute.json
    """
    metadata = metadata or {}

    file_path = Path(file_path)
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    file_folder_name = file_path.stem
    file_output_dir = output_root / file_folder_name
    file_output_dir.mkdir(parents=True, exist_ok=True)

    doc_uuid = str(uuid.uuid4())

    datasource_attr = {
        "document_id": doc_uuid,
        "datasource_name": file_path.name,
        "file_type": file_path.suffix.replace(".", "").upper(),
        "local_path": str(file_path),
        "online_link": metadata.get("url", EPA_LINK),
        "source_page": metadata.get("source_page", ""),
        "summary": metadata.get("summary", ""),
        "author_name": metadata.get("author_name", "Environmental Protection Agency"),
    }

    with (file_output_dir / "attribute.json").open("w", encoding="utf-8") as f:
        json.dump(datasource_attr, f, indent=4)

    for i, chunk in enumerate(chunks):
        chunk_folder = file_output_dir / str(i)
        chunk_folder.mkdir(parents=True, exist_ok=True)

        chunk_uuid = str(uuid.uuid4())

        with (chunk_folder / "content.txt").open("w", encoding="utf-8") as f:
            f.write(chunk.page_content)

        content_type = chunk.metadata.get("content_type", "text")

        chunk_attr = {
            "chunk_id": chunk_uuid,
            "parent_document_id": doc_uuid,
            "page": chunk.metadata.get("page", 0) + 1,
            "chunk_index": i,
            "content_type": content_type,
            "table_index": chunk.metadata.get("table_index"),
            "datasource_name": file_path.name,
            "local_path": str(file_path),
            "online_link": metadata.get("url", EPA_LINK),
            "source_page": metadata.get("source_page", ""),
            "summary": metadata.get("summary", ""),
        }

        with (chunk_folder / "attribute.json").open("w", encoding="utf-8") as f:
            json.dump(chunk_attr, f, indent=4)

    return len(chunks)

@dataclass
class IngestionDocument:
    """Small document object compatible with the existing chunk writer."""
    page_content: str
    metadata: dict


def table_to_markdown(rows):
    """Convert a list of table rows into a simple Markdown table."""
    cleaned_rows = [
        [str(cell or "").replace("\n", " ").strip() for cell in row]
        for row in rows
        if any(str(cell or "").strip() for cell in row)
    ]

    if not cleaned_rows:
        return ""

    max_cols = max(len(row) for row in cleaned_rows)
    normalized = [
        row + [""] * (max_cols - len(row))
        for row in cleaned_rows
    ]

    header = normalized[0]
    separator = ["---"] * max_cols
    body = normalized[1:]

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |",
    ]

    for row in body:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def extract_pdf_table_documents(file_path):
    """Extract PDF tables as table chunks using pdfplumber.

    These are separate from normal PDF text chunks so technical values in
    tables remain searchable downstream.
    """
    import pdfplumber

    table_docs = []

    with pdfplumber.open(str(file_path)) as pdf:
        for page_index, page in enumerate(pdf.pages):
            tables = page.extract_tables() or []

            for table_index, table in enumerate(tables):
                markdown = table_to_markdown(table)
                if not markdown:
                    continue

                table_docs.append(
                    IngestionDocument(
                        page_content=markdown,
                        metadata={
                            "page": page_index,
                            "content_type": "table",
                            "table_index": table_index,
                        },
                    )
                )

    return table_docs


def extract_docx_documents(file_path):
    """Extract DOCX paragraphs and tables as ingestion documents."""
    from docx import Document

    doc = Document(str(file_path))
    documents = []

    paragraph_text = "\n".join(
        paragraph.text.strip()
        for paragraph in doc.paragraphs
        if paragraph.text.strip()
    )

    if paragraph_text:
        documents.append(
            IngestionDocument(
                page_content=paragraph_text,
                metadata={
                    "page": 0,
                    "content_type": "text",
                },
            )
        )

    for table_index, table in enumerate(doc.tables):
        rows = [
            [cell.text.strip() for cell in row.cells]
            for row in table.rows
        ]

        markdown = table_to_markdown(rows)
        if not markdown:
            continue

        documents.append(
            IngestionDocument(
                page_content=markdown,
                metadata={
                    "page": 0,
                    "content_type": "table",
                    "table_index": table_index,
                },
            )
        )

    return documents


def process_pdf(file_path, output_root, metadata=None, chunk_size=1000, chunk_overlap=100):
    """Load one PDF, split text, extract tables, and write chunk files."""
    file_path = Path(file_path)

    loader = PyPDFLoader(str(file_path))
    pages = loader.load()

    splitter = build_splitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    text_chunks = splitter.split_documents(pages)

    for chunk in text_chunks:
        chunk.metadata["content_type"] = "text"

    try:
        table_chunks = extract_pdf_table_documents(file_path)
    except Exception as exc:
        print(f"Warning: failed to extract PDF tables from {file_path.name}: {exc}")
        table_chunks = []

    all_chunks = text_chunks + table_chunks

    return write_chunks_for_document(
        file_path=file_path,
        chunks=all_chunks,
        output_root=output_root,
        metadata=metadata,
    )


def process_docx(file_path, output_root, metadata=None, chunk_size=1000, chunk_overlap=100):
    """Load one DOCX, split paragraph text, extract tables, and write chunk files."""
    file_path = Path(file_path)

    documents = extract_docx_documents(file_path)

    splitter = build_splitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    final_chunks = []

    for doc in documents:
        if doc.metadata.get("content_type") == "table":
            final_chunks.append(doc)
        else:
            split_docs = splitter.split_documents([doc])
            for chunk in split_docs:
                chunk.metadata["content_type"] = "text"
            final_chunks.extend(split_docs)

    return write_chunks_for_document(
        file_path=file_path,
        chunks=final_chunks,
        output_root=output_root,
        metadata=metadata,
    )

def process_file(file_path, output_root, metadata=None, chunk_size=1000, chunk_overlap=100):
    """Dispatch supported files to the correct LangChain/table-aware processor."""
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return process_pdf(
            file_path=file_path,
            output_root=output_root,
            metadata=metadata,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    if suffix == ".docx":
        return process_docx(
            file_path=file_path,
            output_root=output_root,
            metadata=metadata,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    raise ValueError(f"Unsupported file type: {suffix}")

def chunk_with_langchain(source_dir, output_root, chunk_size=1000, chunk_overlap=100):
    """Process all supported files in a raw data directory."""
    source_dir = Path(source_dir)
    output_root = Path(output_root)

    if not source_dir.exists():
        print(f"Source directory not found: {source_dir}")
        return {
            "processed": 0,
            "skipped": 0,
            "failed": 0,
        }

    stats = {
        "processed": 0,
        "skipped": 0,
        "failed": 0,
    }

    for file_path in source_dir.iterdir():
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            stats["skipped"] += 1
            continue

        try:
            count = process_file(
                file_path=file_path,
                output_root=output_root,
                metadata={
                    "url": EPA_LINK,
                    "source_page": "",
                    "summary": "",
                },
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            stats["processed"] += 1
            print(f"Successfully processed {count} chunks for: {file_path.name}")

        except Exception as e:
            stats["failed"] += 1
            print(f"Failed to process {file_path.name}: {str(e)}")

    return stats


def chunk_from_manifest(manifest_path, output_root, chunk_size=1000, chunk_overlap=100):
    """Process downloaded files listed in a scraper manifest.

    Uses each manifest entry's local_path field, which is written by
    rag.manifest.download_manifest().
    """
    entries = load_manifest(manifest_path)

    stats = {
        "processed": 0,
        "skipped_missing_local_path": 0,
        "skipped_missing_file": 0,
        "skipped_unsupported_type": 0,
        "failed": 0,
    }

    for entry in entries:
        if not entry.local_path:
            stats["skipped_missing_local_path"] += 1
            print(f"Skipping manifest entry with no local_path: {entry.url}")
            continue

        file_path = Path(entry.local_path)

        if not file_path.exists():
            stats["skipped_missing_file"] += 1
            print(f"Skipping missing local file: {file_path}")
            continue

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            stats["skipped_unsupported_type"] += 1
            print(f"Skipping unsupported file type: {file_path}")
            continue

        try:
            count = process_file(
                file_path=file_path,
                output_root=output_root,
                metadata={
                    "url": entry.url,
                    "source_page": entry.source_page,
                    "summary": entry.summary,
                },
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            stats["processed"] += 1
            print(f"Successfully processed {count} chunks for: {file_path.name}")

        except Exception as e:
            stats["failed"] += 1
            print(f"Failed to process {file_path.name}: {str(e)}")

    return stats


def parse_args():
    parser = argparse.ArgumentParser(
        description="LangChain ingestion for downloaded Class VI permit documents.",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="Directory of raw downloaded files. Used when --manifest is not provided.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Manifest JSON with local_path values from the downloader.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Directory where chunked ingestion output should be written.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=1000,
        help="LangChain splitter chunk size. Default: 1000.",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=100,
        help="LangChain splitter chunk overlap. Default: 100.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    selected_manifest = args.manifest or manifest_path
    selected_source_dir = args.source_dir or source_dir
    selected_output = args.output or ingestion_folder

    if not selected_output:
        raise ValueError(
            "No output directory provided. Use --output or PATH_TO_CHUNKED_DATA_DIR."
        )

    if selected_manifest:
        stats = chunk_from_manifest(
            manifest_path=selected_manifest,
            output_root=selected_output,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
    elif selected_source_dir:
        stats = chunk_with_langchain(
            source_dir=selected_source_dir,
            output_root=selected_output,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
    else:
        raise ValueError(
            "No input provided. Use --manifest, --source-dir, PATH_TO_MANIFEST, "
            "or PATH_TO_RAW_DATA_DIR."
        )

    print("Ingestion complete.")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()