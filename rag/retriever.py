"""
Schema-aware retriever.

Knows which collection to query for different kinds of review tasks:
- "What does the regulation require?" -> REFERENCE collection
- "How have approved applicants done this?" -> PERMITS collection
- Cross-reference review -> PERMITS with section_id filter

The schema-awareness comes from chunks carrying section_id in metadata
(set during chunking) which the retriever uses as a where-clause filter.
"""

from rag.types import Collection


class Retriever:
    """Coordinates embedding, collection choice, and metadata filtering."""

    def __init__(self, embeddings, store):
        self.embeddings = embeddings
        self.store = store

    def retrieve_reference(self, query_text, section_id="", k=5):
        """Get authoritative regulatory text for a query."""
        return self._retrieve(Collection.REFERENCE, query_text, section_id, k)

    def retrieve_permits(self, query_text, section_id="", k=5):
        """Get precedent text from approved permit applications."""
        return self._retrieve(Collection.PERMITS, query_text, section_id, k)

    def retrieve_both(self, query_text, section_id="", k=5):
        """Query both collections; return a dict keyed by collection."""
        return {
            Collection.REFERENCE: self.retrieve_reference(query_text, section_id, k),
            Collection.PERMITS: self.retrieve_permits(query_text, section_id, k),
        }

    def _retrieve(self, collection, query_text, section_id, k):
        query_vec = self.embeddings.encode_query(query_text)
        where = {"section_id": section_id} if section_id else None
        return self.store.query(collection, query_vec, k=k, where=where)
