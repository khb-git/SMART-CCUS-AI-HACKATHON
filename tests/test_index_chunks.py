import json

from rag.types import Collection, DocumentType


def write_json(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def make_chunked_fixture(tmp_path):
    chunked_dir = tmp_path / "chunked"
    document_dir = chunked_dir / "ADM_Testing_and_Monitoring_Plan"
    chunk_dir = document_dir / "0"

    chunk_dir.mkdir(parents=True)

    write_json(
        document_dir / "attribute.json",
        {
            "datasource_name": "ADM_Testing_and_Monitoring_Plan.pdf",
            "file_type": "PDF",
            "local_path": "data/raw_docs/ADM_Testing_and_Monitoring_Plan.pdf",
            "online_link": "https://example.com/adm_tm.pdf",
            "source_page": "https://example.com/docket",
            "summary": "ADM Testing and Monitoring Plan",
            "plan_type": "testing_monitoring",
            "schema_section_id": "8",
            "schema_section_title": "Testing and Monitoring Plan",
        },
    )

    (chunk_dir / "content.txt").write_text(
        "Monitoring wells will be sampled quarterly.",
        encoding="utf-8",
    )

    write_json(
        chunk_dir / "attribute.json",
        {
            "chunk_id": "chunk-abc",
            "parent_document_id": "doc-123",
            "page": 4,
            "chunk_index": 0,
            "content_type": "table",
            "table_index": 1,
            "sheet_name": "Monitoring",
            "row_start": 1,
            "row_end": 10,
            "datasource_name": "ADM_Testing_and_Monitoring_Plan.pdf",
            "local_path": "data/raw_docs/ADM_Testing_and_Monitoring_Plan.pdf",
            "online_link": "https://example.com/adm_tm.pdf",
            "source_page": "https://example.com/docket",
            "summary": "ADM Testing and Monitoring Plan",
            "plan_type": "testing_monitoring",
            "schema_section_id": "8",
            "schema_section_title": "Testing and Monitoring Plan",
        },
    )

    return chunked_dir


def test_load_chunks_from_chunked_dir_preserves_metadata(tmp_path):
    from rag.index_chunks import load_chunks_from_chunked_dir

    chunked_dir = make_chunked_fixture(tmp_path)

    chunks = load_chunks_from_chunked_dir(
        chunked_dir=chunked_dir,
        collection=Collection.PERMITS,
        project_name="adm",
    )

    assert len(chunks) == 1

    chunk = chunks[0]
    assert chunk.chunk_id == "chunk-abc"
    assert chunk.text == "Monitoring wells will be sampled quarterly."

    metadata = chunk.metadata
    assert metadata.source_document == "ADM_Testing_and_Monitoring_Plan.pdf"
    assert metadata.document_type == DocumentType.PERMIT_APPLICATION
    assert metadata.project_name == "adm"
    assert metadata.section_id == "8"
    assert metadata.schema_section_id == "8"
    assert metadata.schema_section_title == "Testing and Monitoring Plan"
    assert metadata.plan_type == "testing_monitoring"
    assert metadata.content_type == "table"
    assert metadata.table_index == 1
    assert metadata.sheet_name == "Monitoring"
    assert metadata.row_start == 1
    assert metadata.row_end == 10
    assert metadata.local_path.endswith("ADM_Testing_and_Monitoring_Plan.pdf")


def test_reference_collection_uses_epa_guidance_document_type(tmp_path):
    from rag.index_chunks import load_chunks_from_chunked_dir

    chunked_dir = make_chunked_fixture(tmp_path)

    chunks = load_chunks_from_chunked_dir(
        chunked_dir=chunked_dir,
        collection=Collection.REFERENCE,
    )

    assert chunks[0].metadata.document_type == DocumentType.EPA_GUIDANCE


class FakeEmbeddings:
    def __init__(self):
        self.encoded_text_batches = []

    def encode(self, texts):
        self.encoded_text_batches.append(texts)
        return [[1.0, 0.0, 0.0] for _ in texts]


class FakeVectorStore:
    def __init__(self):
        self.add_calls = []

    def add(self, collection, chunks, embeddings):
        self.add_calls.append(
            {
                "collection": collection,
                "chunks": chunks,
                "embeddings": embeddings,
            }
        )
        return len(chunks)


def test_index_chunks_embeds_and_stores_batches(tmp_path):
    from rag.index_chunks import index_chunks, load_chunks_from_chunked_dir

    chunked_dir = make_chunked_fixture(tmp_path)
    chunks = load_chunks_from_chunked_dir(chunked_dir, Collection.PERMITS)

    fake_embeddings = FakeEmbeddings()
    fake_store = FakeVectorStore()

    count = index_chunks(
        chunks=chunks,
        collection=Collection.PERMITS,
        embeddings=fake_embeddings,
        store=fake_store,
        batch_size=1,
    )

    assert count == 1
    assert fake_embeddings.encoded_text_batches == [
        ["Monitoring wells will be sampled quarterly."]
    ]
    assert len(fake_store.add_calls) == 1
    assert fake_store.add_calls[0]["collection"] == Collection.PERMITS
    assert fake_store.add_calls[0]["embeddings"] == [[1.0, 0.0, 0.0]]


def test_load_chunks_skips_empty_content(tmp_path):
    from rag.index_chunks import load_chunks_from_chunked_dir

    chunked_dir = tmp_path / "chunked"
    document_dir = chunked_dir / "doc"
    chunk_dir = document_dir / "0"
    chunk_dir.mkdir(parents=True)

    write_json(document_dir / "attribute.json", {"datasource_name": "doc.pdf"})
    (chunk_dir / "content.txt").write_text("   ", encoding="utf-8")
    write_json(chunk_dir / "attribute.json", {"chunk_index": 0})

    chunks = load_chunks_from_chunked_dir(chunked_dir, Collection.PERMITS)

    assert chunks == []


def test_load_chunks_missing_directory_raises(tmp_path):
    import pytest
    from rag.index_chunks import load_chunks_from_chunked_dir

    with pytest.raises(FileNotFoundError):
        load_chunks_from_chunked_dir(tmp_path / "missing", Collection.PERMITS)

def test_infer_collection_target_prefers_explicit_metadata():
    from rag.index_chunks import infer_collection_target
    from rag.types import Collection

    document_attr = {
        "datasource_name": "anything.pdf",
        "collection_target": "reference",
    }

    assert infer_collection_target(document_attr) == Collection.REFERENCE


def test_infer_collection_target_routes_guidance_to_reference():
    from rag.index_chunks import infer_collection_target
    from rag.types import Collection

    document_attr = {
        "datasource_name": "implementation_manual_508.pdf",
        "summary": "EPA Class VI implementation manual and guidance",
        "online_link": "https://www.epa.gov/uic/final-class-vi-guidance-documents",
    }

    assert infer_collection_target(document_attr) == Collection.REFERENCE


def test_infer_collection_target_routes_permit_plan_to_permits():
    from rag.index_chunks import infer_collection_target
    from rag.types import Collection

    document_attr = {
        "datasource_name": "ADM_Testing_and_Monitoring_Plan.pdf",
        "summary": "ADM Testing and Monitoring Plan",
        "online_link": "https://www.epa.gov/system/files/documents/ADM_Testing_and_Monitoring_Plan.pdf",
    }

    assert infer_collection_target(document_attr) == Collection.PERMITS


def test_load_chunks_from_chunked_dir_auto_routes_chunks(tmp_path):
    from rag.index_chunks import load_chunks_from_chunked_dir_auto
    from rag.types import Collection

    chunked_dir = tmp_path / "chunked"

    reference_doc = chunked_dir / "implementation_manual"
    reference_chunk = reference_doc / "0"
    reference_chunk.mkdir(parents=True)

    write_json(
        reference_doc / "attribute.json",
        {
            "datasource_name": "implementation_manual.pdf",
            "summary": "EPA Class VI implementation manual guidance",
            "online_link": "https://www.epa.gov/uic/final-class-vi-guidance-documents",
        },
    )
    (reference_chunk / "content.txt").write_text("EPA guidance text.", encoding="utf-8")
    write_json(
        reference_chunk / "attribute.json",
        {
            "chunk_id": "reference-chunk",
            "chunk_index": 0,
            "datasource_name": "implementation_manual.pdf",
        },
    )

    permit_doc = chunked_dir / "adm_testing_monitoring"
    permit_chunk = permit_doc / "0"
    permit_chunk.mkdir(parents=True)

    write_json(
        permit_doc / "attribute.json",
        {
            "datasource_name": "ADM_Testing_and_Monitoring_Plan.pdf",
            "summary": "ADM Testing and Monitoring Plan",
            "online_link": "https://www.epa.gov/system/files/documents/ADM_Testing_and_Monitoring_Plan.pdf",
        },
    )
    (permit_chunk / "content.txt").write_text("Permit monitoring text.", encoding="utf-8")
    write_json(
        permit_chunk / "attribute.json",
        {
            "chunk_id": "permit-chunk",
            "chunk_index": 0,
            "datasource_name": "ADM_Testing_and_Monitoring_Plan.pdf",
        },
    )

    routed = load_chunks_from_chunked_dir_auto(chunked_dir)

    assert len(routed[Collection.REFERENCE]) == 1
    assert len(routed[Collection.PERMITS]) == 1
    assert routed[Collection.REFERENCE][0].chunk_id == "reference-chunk"
    assert routed[Collection.PERMITS][0].chunk_id == "permit-chunk"

def test_infer_collection_target_routes_templates_to_reference():
    from rag.index_chunks import infer_collection_target
    from rag.types import Collection

    document_attr = {
        "datasource_name": "tm_plan_template.docx",
        "summary": "Testing and Monitoring Plan template",
        "online_link": "https://www.epa.gov/system/files/documents/tm_plan_template.docx",
        "source_page": "https://www.epa.gov/uic/class-vi-permit-application-templates",
    }

    assert infer_collection_target(document_attr) == Collection.REFERENCE