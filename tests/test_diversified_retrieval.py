import pytest

from rag.types import Chunk, ChunkMetadata, Collection, DocumentType, RetrievalResult


def make_result(source_document, score, chunk_id):
    metadata = ChunkMetadata(
        source_document=source_document,
        document_type=DocumentType.PERMIT_APPLICATION,
        section_id="8",
        page_number=1,
        chunk_index=0,
    )

    return RetrievalResult(
        chunk=Chunk(
            text=f"Text from {source_document}",
            metadata=metadata,
            chunk_id=chunk_id,
        ),
        score=score,
        collection=Collection.PERMITS,
    )


def test_diversify_results_limits_repeated_sources():
    from rag.retriever import diversify_results_by_source

    results = [
        make_result("one_earth.pdf", 0.90, "one-earth-1"),
        make_result("one_earth.pdf", 0.89, "one-earth-2"),
        make_result("adm.pdf", 0.88, "adm-1"),
        make_result("hgcs.pdf", 0.87, "hgcs-1"),
    ]

    diversified = diversify_results_by_source(
        results,
        k=3,
        max_per_source=1,
    )

    assert [result.chunk.chunk_id for result in diversified] == [
        "one-earth-1",
        "adm-1",
        "hgcs-1",
    ]


def test_diversify_results_allows_multiple_per_source():
    from rag.retriever import diversify_results_by_source

    results = [
        make_result("one_earth.pdf", 0.90, "one-earth-1"),
        make_result("one_earth.pdf", 0.89, "one-earth-2"),
        make_result("one_earth.pdf", 0.88, "one-earth-3"),
        make_result("adm.pdf", 0.87, "adm-1"),
    ]

    diversified = diversify_results_by_source(
        results,
        k=3,
        max_per_source=2,
    )

    assert [result.chunk.chunk_id for result in diversified] == [
        "one-earth-1",
        "one-earth-2",
        "adm-1",
    ]


def test_diversify_results_rejects_invalid_max_per_source():
    from rag.retriever import diversify_results_by_source

    with pytest.raises(ValueError, match="max_per_source"):
        diversify_results_by_source([], k=5, max_per_source=0)


class FakeEmbeddings:
    def encode_query(self, query_text):
        return [0.1, 0.2, 0.3]


class FakeStore:
    def __init__(self):
        self.query_calls = []

    def query(self, collection, query_embedding, k=5, where=None):
        self.query_calls.append(
            {
                "collection": collection,
                "query_embedding": query_embedding,
                "k": k,
                "where": where,
            }
        )

        return [
            make_result("one_earth.pdf", 0.90, "one-earth-1"),
            make_result("one_earth.pdf", 0.89, "one-earth-2"),
            make_result("adm.pdf", 0.88, "adm-1"),
            make_result("hgcs.pdf", 0.87, "hgcs-1"),
        ]


def test_retriever_fetches_extra_results_before_diversifying():
    from rag.retriever import Retriever

    store = FakeStore()
    retriever = Retriever(embeddings=FakeEmbeddings(), store=store)

    results = retriever.retrieve_permits_diversified(
        "How do applicants monitor injection pressure?",
        section_id="8",
        k=2,
        fetch_k=10,
        max_per_source=1,
    )

    assert [result.chunk.chunk_id for result in results] == [
        "one-earth-1",
        "adm-1",
    ]

    assert store.query_calls[0]["collection"] == Collection.PERMITS
    assert store.query_calls[0]["k"] == 10
    assert store.query_calls[0]["where"] == {"section_id": "8"}