"""
Vector store with two collections: permits and reference.

Why two collections:
- A retrieval for "what does the regulation say about casing" should not
  return an applicant's casing description.
- A retrieval for "how have approved applicants handled fracture pressure"
  should not return CFR text.

The retriever chooses which collection to query based on the review task.
"""

import logging
from pathlib import Path

from rag.types import Chunk, ChunkMetadata, Collection, DocumentType, RetrievalResult

logger = logging.getLogger(__name__)


class VectorStore:
    """Chroma-backed vector store with separate collections for permits/reference."""

    def __init__(self, persist_directory="./chroma_data", client=None):
        self.persist_directory = str(Path(persist_directory))
        self._client = client
        self._collections = {}

        if self._client is not None:
            self._initialize_collections()

    def _connect(self):
        """Lazy-connect to Chroma and initialize collections."""
        if self._client is not None and self._collections:
            return

        if self._client is None:
            try:
                import chromadb
            except ImportError as exc:
                raise ImportError(
                    "chromadb is required for vector storage. "
                    "Install dependencies with `pip install -r requirements.txt`."
                ) from exc

            self._client = chromadb.PersistentClient(path=self.persist_directory)

        self._initialize_collections()

    def _initialize_collections(self):
        """Create or load the standard RAG collections."""
        for collection in Collection:
            self._collections[collection] = self._client.get_or_create_collection(
                name=collection.value,
                metadata={"hnsw:space": "cosine"},
            )

    def _get_collection(self, collection):
        """Normalize and return a Chroma collection."""
        self._connect()

        try:
            collection = Collection(collection)
        except ValueError as exc:
            valid = ", ".join(c.value for c in Collection)
            raise ValueError(f"Unknown collection '{collection}'. Valid: {valid}") from exc

        return self._collections[collection]

    @staticmethod
    def _chunk_id(chunk, fallback_index=0):
        """Get a stable chunk id for Chroma."""
        if chunk.chunk_id:
            return chunk.chunk_id

        metadata = chunk.metadata
        source = metadata.source_document or "unknown_source"
        return f"{source}:{metadata.chunk_index}:{fallback_index}"

    def add(self, collection, chunks, embeddings):
        """Add chunks and their vectors to a collection.

        Args:
            collection: Collection.PERMITS or Collection.REFERENCE.
            chunks: list[Chunk].
            embeddings: list[list[float]].

        Returns:
            Number of chunks added.
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Got {len(chunks)} chunks but {len(embeddings)} embeddings"
            )

        if not chunks:
            return 0

        chroma_collection = self._get_collection(collection)

        ids = [
            self._chunk_id(chunk, fallback_index=i)
            for i, chunk in enumerate(chunks)
        ]
        documents = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata.to_dict() for chunk in chunks]

        chroma_collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        logger.info("Added %d chunks to collection '%s'", len(chunks), collection)
        return len(chunks)

    def query(self, collection, query_embedding, k=5, where=None):
        """Return the top-k most similar chunks from a collection.

        Args:
            collection: Collection.PERMITS or Collection.REFERENCE.
            query_embedding: vector for the query.
            k: number of results.
            where: optional Chroma metadata filter.

        Returns:
            list[RetrievalResult].
        """
        chroma_collection = self._get_collection(collection)

        results = chroma_collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where=where,
        )

        ids = (results.get("ids") or [[]])[0]
        documents = (results.get("documents") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]

        retrieval_results = []

        for i, document in enumerate(documents):
            metadata_dict = metadatas[i] if i < len(metadatas) else {}
            distance = distances[i] if i < len(distances) else None
            chunk_id = ids[i] if i < len(ids) else ""

            chunk = Chunk(
                text=document,
                metadata=self._metadata_from_dict(metadata_dict),
                chunk_id=chunk_id,
            )

            # Chroma cosine distance: smaller is better. Convert to a similarity-like
            # score for downstream display.
            score = 1.0 - float(distance) if distance is not None else 0.0

            retrieval_results.append(
                RetrievalResult(
                    chunk=chunk,
                    score=score,
                    collection=Collection(collection),
                )
            )

        return retrieval_results

    @staticmethod
    def _metadata_from_dict(metadata):
        """Rehydrate ChunkMetadata from Chroma metadata."""
        document_type_value = metadata.get(
            "document_type",
            DocumentType.PERMIT_APPLICATION.value,
        )

        try:
            document_type = DocumentType(document_type_value)
        except ValueError:
            document_type = DocumentType.PERMIT_APPLICATION

        return ChunkMetadata(
            source_document=metadata.get("source_document", ""),
            document_type=document_type,
            project_name=metadata.get("project_name", ""),
            section_id=metadata.get("section_id", ""),
            subsection_id=metadata.get("subsection_id", ""),
            page_number=int(metadata.get("page_number", 0) or 0),
            chunk_index=int(metadata.get("chunk_index", 0) or 0),
            cfr_citation=metadata.get("cfr_citation", ""),
        )