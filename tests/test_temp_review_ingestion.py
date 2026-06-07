from pathlib import Path


def test_is_supported_review_file():
    from review.temp_ingestion import is_supported_review_file

    assert is_supported_review_file("plan.pdf")
    assert is_supported_review_file("plan.docx")
    assert is_supported_review_file("plan.xlsx")
    assert not is_supported_review_file("plan.txt")


def test_convert_ingestion_chunks():
    from review.temp_ingestion import convert_ingestion_chunks

    class FakeChunk:
        page_content = "Temporary review text."
        metadata = {"page": 1, "content_type": "text"}

    chunks = convert_ingestion_chunks([FakeChunk()])

    assert len(chunks) == 1
    assert chunks[0].text == "Temporary review text."
    assert chunks[0].metadata["page"] == 1
    assert chunks[0].metadata["content_type"] == "text"


def test_ingest_review_document_temporarily_rejects_unsupported_file(tmp_path):
    import pytest

    from review.temp_ingestion import ingest_review_document_temporarily

    file_path = tmp_path / "notes.txt"
    file_path.write_text("not supported", encoding="utf-8")

    with pytest.raises(ValueError):
        ingest_review_document_temporarily(file_path)


def test_ingest_review_document_temporarily_cleans_up(monkeypatch, tmp_path):
    from review.temp_ingestion import ingest_review_document_temporarily

    source_file = tmp_path / "review.docx"
    source_file.write_text("fake docx content", encoding="utf-8")

    class FakeChunk:
        page_content = "Extracted review content."
        metadata = {"content_type": "text", "page": 1}

    def fake_process_temporary_file(
            file_path,
            output_root,
            chunk_size=1000,
            chunk_overlap=100,
    ):
        assert Path(file_path).exists()
        output_root = Path(output_root)
        chunk_dir = output_root / "review" / "0"
        chunk_dir.mkdir(parents=True, exist_ok=True)
        (chunk_dir / "content.txt").write_text("Extracted review content.", encoding="utf-8")
        (chunk_dir / "attribute.json").write_text(
            '{"content_type": "text", "page": 1}',
            encoding="utf-8",
        )
        return 1

    monkeypatch.setattr(
        "review.temp_ingestion.process_temporary_file",
        fake_process_temporary_file,
    )

    document = ingest_review_document_temporarily(source_file)

    assert document.original_filename == "review.docx"
    assert document.file_extension == ".docx"
    assert document.total_chunks() == 1
    assert document.combined_text() == "Extracted review content."

    # Temporary paths are intentionally cleared after cleanup.
    assert document.temporary_directory == ""
    assert document.temporary_file_path == ""


def test_ingest_review_document_temporarily_can_keep_artifacts_for_debug(
    monkeypatch,
    tmp_path,
):
    from review.temp_ingestion import ingest_review_document_temporarily

    source_file = tmp_path / "review.pdf"
    source_file.write_bytes(b"%PDF fake")

    class FakeChunk:
        page_content = "Extracted PDF content."
        metadata = {"content_type": "text", "page": 1}

    def fake_process_temporary_file(
            file_path,
            output_root,
            chunk_size=1000,
            chunk_overlap=100,
    ):
        assert Path(file_path).exists()
        output_root = Path(output_root)
        chunk_dir = output_root / "review" / "0"
        chunk_dir.mkdir(parents=True, exist_ok=True)
        (chunk_dir / "content.txt").write_text("Extracted review content.", encoding="utf-8")
        (chunk_dir / "attribute.json").write_text(
            '{"content_type": "text", "page": 1}',
            encoding="utf-8",
        )
        return 1

    monkeypatch.setattr(
        "review.temp_ingestion.process_temporary_file",
        fake_process_temporary_file,
    )

    document = ingest_review_document_temporarily(
        source_file,
        keep_temporary_artifacts=True,
    )

    assert document.total_chunks() == 1
    assert document.temporary_directory
    assert document.temporary_file_path
    assert Path(document.temporary_file_path).exists()

    # Manual cleanup for this debug mode test.
    import shutil

    shutil.rmtree(document.temporary_directory)

def test_load_chunks_from_temporary_output(tmp_path):
    from review.temp_ingestion import load_chunks_from_temporary_output

    chunk_dir = tmp_path / "doc" / "0"
    chunk_dir.mkdir(parents=True)

    (chunk_dir / "content.txt").write_text("Temporary chunk text.", encoding="utf-8")
    (chunk_dir / "attribute.json").write_text(
        '{"content_type": "text", "page": 3}',
        encoding="utf-8",
    )

    chunks = load_chunks_from_temporary_output(tmp_path)

    assert len(chunks) == 1
    assert chunks[0].text == "Temporary chunk text."
    assert chunks[0].metadata["content_type"] == "text"
    assert chunks[0].metadata["page"] == 3