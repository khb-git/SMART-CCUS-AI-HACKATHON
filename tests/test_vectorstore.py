import pytest

from rag.types import Chunk, ChunkMetadata, Collection, DocumentType


class FakeChromaCollection:
    def __init__(self, name):
        self.name = name
        self.add_calls = []
        self.query_calls = []
        self.query_response = {
            "ids": [["chunk-1"]],
            "documents": [["Stored chunk text"]],
            "metadatas": [[
                {
                    "source_document": "adm.pdf",
                    "document_type": "permit_application",
                    "project_name": "adm",
                    "section_id": "8",
                    "subsection_id": "",
                    "page_number": 4,
                    "chunk_index": 2,
                    "cfr_citation": "",
                }
            ]],
            "distances": [[0.25]],
        }

    def add(self, ids, documents, metadatas, embeddings):
        self.add_calls.append(
            {
                "ids": ids,
                "documents": documents,
                "metadatas": metadatas,
                "embeddings": embeddings,
            }
        )

    def query(self, query_embeddings, n_results, where=None):
        self.query_calls.append(
            {
                "query_embeddings": query_embeddings,
                "n_results": n_results,
                "where": where,
            }
        )
        return self.query_response


class FakeChromaClient:
    def __init__(self):
        self.collections = {}

    def get_or_create_collection(self, name, metadata=None):
        if name not in self.collections:
            self.collections[name] = FakeChromaCollection(name)
        return self.collections[name]


def make_chunk(text="Permit chunk", chunk_id="chunk-1"):
    metadata = ChunkMetadata(
        source_document="adm.pdf",
        document_type=DocumentType.PERMIT_APPLICATION,
        project_name="adm",
        section_id="8",
        page_number=4,
        chunk_index=2,
    )
    return Chunk(text=text, metadata=metadata, chunk_id=chunk_id)


def test_vectorstore_initializes_two_collections():
    from rag.vectorstore import VectorStore

    client = FakeChromaClient()
    store = VectorStore(client=client)

    assert "permits" in client.collections
    assert "reference" in client.collections
    assert store._collections[Collection.PERMITS].name == "permits"
    assert store._collections[Collection.REFERENCE].name == "reference"


def test_add_stores_chunks_with_metadata_and_embeddings():
    from rag.vectorstore import VectorStore

    client = FakeChromaClient()
    store = VectorStore(client=client)

    chunk = make_chunk()
    embedding = [0.1, 0.2, 0.3]

    count = store.add(
        Collection.PERMITS,
        chunks=[chunk],
        embeddings=[embedding],
    )

    assert count == 1

    collection = client.collections["permits"]
    call = collection.add_calls[0]

    assert call["ids"] == ["chunk-1"]
    assert call["documents"] == ["Permit chunk"]
    assert call["embeddings"] == [[0.1, 0.2, 0.3]]
    assert call["metadatas"][0]["source_document"] == "adm.pdf"
    assert call["metadatas"][0]["document_type"] == "permit_application"
    assert call["metadatas"][0]["section_id"] == "8"


def test_add_rejects_chunk_embedding_length_mismatch():
    from rag.vectorstore import VectorStore

    store = VectorStore(client=FakeChromaClient())

    with pytest.raises(ValueError, match="chunks but"):
        store.add(
            Collection.PERMITS,
            chunks=[make_chunk()],
            embeddings=[],
        )


def test_add_empty_list_returns_zero():
    from rag.vectorstore import VectorStore

    store = VectorStore(client=FakeChromaClient())

    assert store.add(Collection.PERMITS, chunks=[], embeddings=[]) == 0


def test_query_returns_retrieval_results():
    from rag.vectorstore import VectorStore

    client = FakeChromaClient()
    store = VectorStore(client=client)

    results = store.query(
        Collection.PERMITS,
        query_embedding=[0.1, 0.2, 0.3],
        k=3,
        where={"section_id": "8"},
    )

    assert len(results) == 1

    result = results[0]
    assert result.collection == Collection.PERMITS
    assert result.chunk.chunk_id == "chunk-1"
    assert result.chunk.text == "Stored chunk text"
    assert result.chunk.metadata.source_document == "adm.pdf"
    assert result.chunk.metadata.section_id == "8"
    assert result.chunk.metadata.page_number == 4
    assert result.score == pytest.approx(0.75)

    query_call = client.collections["permits"].query_calls[0]
    assert query_call["query_embeddings"] == [[0.1, 0.2, 0.3]]
    assert query_call["n_results"] == 3
    assert query_call["where"] == {"section_id": "8"}


def test_unknown_collection_raises_error():
    from rag.vectorstore import VectorStore

    store = VectorStore(client=FakeChromaClient())

    with pytest.raises(ValueError, match="Unknown collection"):
        store.query("not_a_collection", query_embedding=[0.1], k=1)


def test_metadata_sanitization_removes_none_values():
    from rag.vectorstore import VectorStore

    raw_metadata = {
        "source_document": "doc.pdf",
        "table_index": None,
        "sheet_name": None,
        "page_number": 1,
    }

    sanitized = VectorStore._sanitize_metadata(raw_metadata)

    assert sanitized["source_document"] == "doc.pdf"
    assert sanitized["table_index"] == ""
    assert sanitized["sheet_name"] == ""
    assert sanitized["page_number"] == 1