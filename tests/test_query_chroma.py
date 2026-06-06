from rag.types import Chunk, ChunkMetadata, Collection, DocumentType, RetrievalResult


def test_format_result_includes_metadata():
    from rag.query_chroma import format_result

    metadata = ChunkMetadata(
        source_document="implementation_manual.pdf",
        document_type=DocumentType.EPA_GUIDANCE,
        page_number=12,
        chunk_index=3,
        content_type="table",
        plan_type="testing_monitoring",
        schema_section_id="8",
        schema_section_title="Testing and Monitoring Plan",
        online_link="https://example.com/manual.pdf",
        source_page="https://example.com/docket",
    )

    result = RetrievalResult(
        chunk=Chunk(
            text="Monitoring requirements include pressure monitoring.",
            metadata=metadata,
            chunk_id="chunk-1",
        ),
        score=0.87,
        collection=Collection.REFERENCE,
    )

    output = format_result(result, 1)

    assert "Result 1" in output
    assert "Score: 0.8700" in output
    assert "implementation_manual.pdf" in output
    assert "Content type: table" in output
    assert "Schema section: 8 Testing and Monitoring Plan" in output
    assert "Monitoring requirements" in output


def test_query_collection_uses_reference_retriever(monkeypatch):
    import rag.query_chroma as query_module

    calls = {}

    class FakeEmbeddings:
        def __init__(self, model_name):
            calls["model_name"] = model_name

    class FakeVectorStore:
        def __init__(self, persist_directory):
            calls["persist_directory"] = persist_directory

    class FakeRetriever:
        def __init__(self, embeddings, store):
            calls["retriever_created"] = True

        def retrieve_reference(self, query, section_id="", k=5):
            calls["query"] = query
            calls["section_id"] = section_id
            calls["k"] = k
            return ["reference-result"]

        def retrieve_permits(self, query, section_id="", k=5):
            return ["permit-result"]

    monkeypatch.setattr(query_module, "Embeddings", FakeEmbeddings)
    monkeypatch.setattr(query_module, "VectorStore", FakeVectorStore)
    monkeypatch.setattr(query_module, "Retriever", FakeRetriever)

    results = query_module.query_collection(
        query="testing and monitoring",
        collection=query_module.Collection.REFERENCE,
        persist_directory="fake_chroma",
        model_name="fake-model",
        k=3,
        section_id="8",
    )

    assert results == ["reference-result"]
    assert calls["model_name"] == "fake-model"
    assert calls["persist_directory"] == "fake_chroma"
    assert calls["query"] == "testing and monitoring"
    assert calls["section_id"] == "8"
    assert calls["k"] == 3


def test_query_collection_uses_permit_retriever(monkeypatch):
    import rag.query_chroma as query_module

    class FakeEmbeddings:
        def __init__(self, model_name):
            pass

    class FakeVectorStore:
        def __init__(self, persist_directory):
            pass

    class FakeRetriever:
        def __init__(self, embeddings, store):
            pass

        def retrieve_reference(self, query, section_id="", k=5):
            return ["reference-result"]

        def retrieve_permits(self, query, section_id="", k=5):
            return ["permit-result"]

    monkeypatch.setattr(query_module, "Embeddings", FakeEmbeddings)
    monkeypatch.setattr(query_module, "VectorStore", FakeVectorStore)
    monkeypatch.setattr(query_module, "Retriever", FakeRetriever)

    results = query_module.query_collection(
        query="well construction casing",
        collection=query_module.Collection.PERMITS,
        persist_directory="fake_chroma",
        model_name="fake-model",
        k=2,
    )

    assert results == ["permit-result"]