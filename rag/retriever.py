"""
Schema-aware retriever.

Knows which collection to query for different kinds of review tasks:
- "What does the regulation require?" -> REFERENCE collection
- "How have approved applicants done this?" -> PERMITS collection
- Cross-reference review -> PERMITS with section_id filter

The schema-awareness comes from chunks carrying section_id in metadata
which the retriever uses as a where-clause filter.
"""

from collections import defaultdict

from rag.types import Collection


class Retriever:
    """Coordinates embedding, collection choice, metadata filtering, and result shaping."""

    def __init__(self, embeddings, store):
        self.embeddings = embeddings
        self.store = store

    def retrieve_reference(self, query_text, section_id="", k=5):
        """Get authoritative regulatory/reference text for a query."""
        return self._retrieve(Collection.REFERENCE, query_text, section_id, k)

    def retrieve_permits(self, query_text, section_id="", k=5):
        """Get precedent text from approved permit applications."""
        return self._retrieve(Collection.PERMITS, query_text, section_id, k)

    def retrieve_reference_diversified(
        self,
        query_text,
        section_id="",
        k=5,
        fetch_k=30,
        max_per_source=1,
    ):
        """Get diversified reference results."""
        return self._retrieve_diversified(
            Collection.REFERENCE,
            query_text,
            section_id=section_id,
            k=k,
            fetch_k=fetch_k,
            max_per_source=max_per_source,
        )

    def retrieve_permits_diversified(
        self,
        query_text,
        section_id="",
        k=5,
        fetch_k=30,
        max_per_source=1,
    ):
        """Get diversified permit precedent results."""
        return self._retrieve_diversified(
            Collection.PERMITS,
            query_text,
            section_id=section_id,
            k=k,
            fetch_k=fetch_k,
            max_per_source=max_per_source,
        )

    def retrieve_both(self, query_text, section_id="", k=5):
        """Query both collections; return a dict keyed by collection."""
        return {
            Collection.REFERENCE: self.retrieve_reference(query_text, section_id, k),
            Collection.PERMITS: self.retrieve_permits(query_text, section_id, k),
        }

    def retrieve_both_diversified(
        self,
        query_text,
        section_id="",
        k=5,
        fetch_k=30,
        max_per_source=1,
    ):
        """Query both collections with diversified results."""
        return {
            Collection.REFERENCE: self.retrieve_reference_diversified(
                query_text,
                section_id=section_id,
                k=k,
                fetch_k=fetch_k,
                max_per_source=max_per_source,
            ),
            Collection.PERMITS: self.retrieve_permits_diversified(
                query_text,
                section_id=section_id,
                k=k,
                fetch_k=fetch_k,
                max_per_source=max_per_source,
            ),
        }

    def _retrieve(self, collection, query_text, section_id, k):
        query_vec = self.embeddings.encode_query(query_text)
        where = {"section_id": section_id} if section_id else None
        return self.store.query(collection, query_vec, k=k, where=where)

    def _retrieve_diversified(
        self,
        collection,
        query_text,
        section_id="",
        k=5,
        fetch_k=30,
        max_per_source=1,
    ):
        """Retrieve more results, then diversify by source document.

        This avoids returning many near-duplicate chunks from the same PDF/DOCX/XLSX.
        """
        if fetch_k < k:
            fetch_k = k

        raw_results = self._retrieve(
            collection=collection,
            query_text=query_text,
            section_id=section_id,
            k=fetch_k,
        )

        return diversify_results_by_source(
            raw_results,
            k=k,
            max_per_source=max_per_source,
        )


def source_key_for_result(result):
    """Choose the grouping key used for result diversification."""
    metadata = result.chunk.metadata

    return (
        metadata.source_document
        or metadata.local_path
        or metadata.online_link
        or result.chunk.chunk_id
        or "unknown_source"
    )


def diversify_results_by_source(results, k=5, max_per_source=1):
    """Keep the best scoring results while limiting repeats per source document.

    Args:
        results: ranked retrieval results.
        k: final number of results to return.
        max_per_source: max chunks allowed from the same source document.

    Returns:
        Diversified list of retrieval results.
    """
    if k <= 0:
        return []

    if max_per_source <= 0:
        raise ValueError("max_per_source must be greater than 0")

    diversified = []
    source_counts = defaultdict(int)

    for result in results:
        source_key = source_key_for_result(result)

        if source_counts[source_key] >= max_per_source:
            continue

        diversified.append(result)
        source_counts[source_key] += 1

        if len(diversified) >= k:
            break

    return diversified