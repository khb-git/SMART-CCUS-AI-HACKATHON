import json
from pathlib import Path


class FakeDocument:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}


def test_chunk_from_manifest_processes_local_pdf(tmp_path, monkeypatch):
    import ingestion.main as ingestion_main

    raw_dir = tmp_path / "raw_docs"
    raw_dir.mkdir()

    pdf_path = raw_dir / "permit__abc123.pdf"
    pdf_path.write_bytes(b"%PDF fake content")

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps([
            {
                "summary": "ADM Decatur permit application",
                "url": "https://example.com/permit.pdf",
                "source_page": "https://example.com/docket",
                "local_path": str(pdf_path),
            }
        ]),
        encoding="utf-8",
    )

    output_dir = tmp_path / "chunked"

    class FakeLoader:
        def __init__(self, path):
            self.path = path

        def load(self):
            return [
                FakeDocument(
                    page_content="This is page one text.",
                    metadata={"page": 0},
                )
            ]

    class FakeSplitter:
        def __init__(self, chunk_size=1000, chunk_overlap=100, add_start_index=True):
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
            self.add_start_index = add_start_index

        def split_documents(self, pages):
            return [
                FakeDocument(
                    page_content="This is chunk one.",
                    metadata={"page": 0},
                )
            ]

    monkeypatch.setattr(ingestion_main, "PyPDFLoader", FakeLoader)
    monkeypatch.setattr(ingestion_main, "RecursiveCharacterTextSplitter", FakeSplitter)

    stats = ingestion_main.chunk_from_manifest(
        manifest_path=manifest_path,
        output_root=output_dir,
    )

    assert stats["processed"] == 1
    assert stats["failed"] == 0

    document_dir = output_dir / "permit__abc123"
    assert document_dir.exists()

    document_attr = json.loads(
        (document_dir / "attribute.json").read_text(encoding="utf-8")
    )

    assert document_attr["datasource_name"] == "permit__abc123.pdf"
    assert document_attr["local_path"] == str(pdf_path)
    assert document_attr["online_link"] == "https://example.com/permit.pdf"
    assert document_attr["source_page"] == "https://example.com/docket"
    assert document_attr["summary"] == "ADM Decatur permit application"

    chunk_text = (document_dir / "0" / "content.txt").read_text(encoding="utf-8")
    assert chunk_text == "This is chunk one."

    chunk_attr = json.loads(
        (document_dir / "0" / "attribute.json").read_text(encoding="utf-8")
    )
    assert chunk_attr["datasource_name"] == "permit__abc123.pdf"
    assert chunk_attr["local_path"] == str(pdf_path)
    assert chunk_attr["online_link"] == "https://example.com/permit.pdf"


def test_chunk_from_manifest_skips_missing_local_path(tmp_path):
    import ingestion.main as ingestion_main

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps([
            {
                "summary": "No local path yet",
                "url": "https://example.com/permit.pdf",
                "source_page": "https://example.com/docket",
            }
        ]),
        encoding="utf-8",
    )

    output_dir = tmp_path / "chunked"

    stats = ingestion_main.chunk_from_manifest(
        manifest_path=manifest_path,
        output_root=output_dir,
    )

    assert stats["processed"] == 0
    assert stats["skipped_missing_local_path"] == 1


def test_chunk_from_manifest_skips_missing_file(tmp_path):
    import ingestion.main as ingestion_main

    missing_pdf = tmp_path / "raw_docs" / "missing.pdf"

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps([
            {
                "summary": "Missing local file",
                "url": "https://example.com/missing.pdf",
                "source_page": "https://example.com/docket",
                "local_path": str(missing_pdf),
            }
        ]),
        encoding="utf-8",
    )

    output_dir = tmp_path / "chunked"

    stats = ingestion_main.chunk_from_manifest(
        manifest_path=manifest_path,
        output_root=output_dir,
    )

    assert stats["processed"] == 0
    assert stats["skipped_missing_file"] == 1


def test_chunk_from_manifest_skips_unsupported_file_type(tmp_path):
    import ingestion.main as ingestion_main

    raw_dir = tmp_path / "raw_docs"
    raw_dir.mkdir()

    xlsx_path = raw_dir / "permit.xlsx"
    xlsx_path.write_text("fake xlsx placeholder", encoding="utf-8")

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps([
            {
                "summary": "Unsupported for current ingestion",
                "url": "https://example.com/permit.docx",
                "source_page": "https://example.com/docket",
                "local_path": str(xlsx_path),
            }
        ]),
        encoding="utf-8",
    )

    output_dir = tmp_path / "chunked"

    stats = ingestion_main.chunk_from_manifest(
        manifest_path=manifest_path,
        output_root=output_dir,
    )

    assert stats["processed"] == 0
    assert stats["skipped_unsupported_type"] == 1