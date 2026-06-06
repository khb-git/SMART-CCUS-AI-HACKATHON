def test_looks_like_section_heading_detects_numbered_heading():
    import ingestion.main as ingestion_main

    assert ingestion_main.looks_like_section_heading(
        "3.2 Injection Rate and Pressure Monitoring"
    )


def test_annotate_documents_with_section_context_applies_heading():
    import ingestion.main as ingestion_main

    doc = ingestion_main.IngestionDocument(
        page_content=(
            "3.2 Injection Rate and Pressure Monitoring\n"
            "Flow will be monitored with a mass flowmeter."
        ),
        metadata={"page": 0, "content_type": "text"},
    )

    annotated = ingestion_main.annotate_documents_with_section_context([doc])

    assert annotated[0].metadata["section_heading"] == (
        "3.2 Injection Rate and Pressure Monitoring"
    )
    assert annotated[0].metadata["local_section_title"] == (
        "3.2 Injection Rate and Pressure Monitoring"
    )
    assert annotated[0].metadata["detected_heading_on_page"] == (
        "3.2 Injection Rate and Pressure Monitoring"
    )


def test_add_section_context_to_chunks_prepends_context():
    import ingestion.main as ingestion_main

    chunk = ingestion_main.IngestionDocument(
        page_content="Flow will be monitored with a mass flowmeter.",
        metadata={
            "page": 0,
            "content_type": "text",
            "section_heading": "3.2 Injection Rate and Pressure Monitoring",
        },
    )

    updated = ingestion_main.add_section_context_to_chunks([chunk])

    assert updated[0].page_content.startswith(
        "Section context: 3.2 Injection Rate and Pressure Monitoring"
    )
    assert "Flow will be monitored" in updated[0].page_content


def test_write_chunks_preserves_section_context_metadata(tmp_path):
    import json
    import ingestion.main as ingestion_main

    file_path = tmp_path / "testing_monitoring.pdf"
    file_path.write_bytes(b"%PDF fake")

    chunk = ingestion_main.IngestionDocument(
        page_content="Section context: 3.2 Injection Rate and Pressure Monitoring\n\nFlow text.",
        metadata={
            "page": 0,
            "content_type": "text",
            "section_heading": "3.2 Injection Rate and Pressure Monitoring",
            "local_section_title": "3.2 Injection Rate and Pressure Monitoring",
            "detected_heading_on_page": "3.2 Injection Rate and Pressure Monitoring",
        },
    )

    output_dir = tmp_path / "chunked"

    count = ingestion_main.write_chunks_for_document(
        file_path=file_path,
        chunks=[chunk],
        output_root=output_dir,
        metadata={
            "url": "https://example.com/testing_monitoring.pdf",
            "source_page": "https://example.com/docket",
            "summary": "Testing and Monitoring Plan",
        },
    )

    assert count == 1

    attr = json.loads(
        (output_dir / "testing_monitoring" / "0" / "attribute.json").read_text(
            encoding="utf-8"
        )
    )

    assert attr["section_heading"] == "3.2 Injection Rate and Pressure Monitoring"
    assert attr["local_section_title"] == "3.2 Injection Rate and Pressure Monitoring"
    assert attr["detected_heading_on_page"] == (
        "3.2 Injection Rate and Pressure Monitoring"
    )


def test_chunk_metadata_preserves_section_context():
    from rag.types import ChunkMetadata, DocumentType

    metadata = ChunkMetadata(
        source_document="doc.pdf",
        document_type=DocumentType.PERMIT_APPLICATION,
        section_heading="3.2 Injection Rate and Pressure Monitoring",
        local_section_title="3.2 Injection Rate and Pressure Monitoring",
        detected_heading_on_page="3.2 Injection Rate and Pressure Monitoring",
    )

    data = metadata.to_dict()

    assert data["section_heading"] == "3.2 Injection Rate and Pressure Monitoring"
    assert data["local_section_title"] == (
        "3.2 Injection Rate and Pressure Monitoring"
    )
    assert data["detected_heading_on_page"] == (
        "3.2 Injection Rate and Pressure Monitoring"
    )