"""
Vector store with two collections: permits and reference.

Why two collections (not one with a metadata filter)?
- A retrieval for "what does the regulation say about casing" must never
  return an applicant's casing description.
- A retrieval for "how have approved applicants handled fracture pressure"
  must never return CFR text.

The retriever picks which collection to query based on the review task.
"""

import logging

from rag.types import Collection

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector store with separate collections for permits and reference."""

    def __init__(self, persist_directory="./chroma_data"):
        self.persist_directory = persist_directory
        self._client = None
        self._collections = {}

    def _connect(self):
        if self._client is not None:
            return
        # TODO: import chromadb
        #       self._client = chromadb.PersistentClient(path=self.persist_directory)
        #       for c in Collection:
        #           self._collections[c] = self._client.get_or_create_collection(
        #               name=c.value, metadata={"hnsw:space": "cosine"})
        logger.warning("VectorStore._connect not yet implemented")

    def add(self, collection, chunks, embeddings):
        """Add chunks and their vectors to a collection."""
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Got {len(chunks)} chunks but {len(embeddings)} embeddings"
            )
        self._connect()
        # TODO: self._collections[collection].add(
        #           ids=[c.chunk_id or str(i) for i, c in enumerate(chunks)],
        #           documents=[c.text for c in chunks],
        #           metadatas=[c.metadata.to_dict() for c in chunks],
        #           embeddings=embeddings,
        #       )

    def query(self, collection, query_embedding, k=5, where=None):
        """Return the top-k most similar chunks from a collection.

        Args:
            collection: Collection.PERMITS or Collection.REFERENCE.
            query_embedding: the vector to search with.
            k: number of results to return.
            where: optional metadata filter, e.g. {"section_id": "section_07"}.
        """
        self._connect()
        # TODO: results = self._collections[collection].query(
        #           query_embeddings=[query_embedding], n_results=k, where=where)
        #       return [RetrievalResult(...) for row in results]
        return []
