"""
Ingestion pipeline: load -> chunk -> embed -> store.

Runs offline, once per document. Separate from the online retrieval/
generation path because the two have different performance profiles.
"""

import logging
from pathlib import Path

from rag.chunker import chunk_document
from rag.embeddings import Embeddings
from rag.loaders import load_document
from rag.types import Collection, DocumentType
from rag.vectorstore import VectorStore

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Load -> chunk -> embed -> store, one document at a time."""

    def __init__(self, embeddings=None, store=None):
        self.embeddings = embeddings or Embeddings()
        self.store = store or VectorStore()

    def ingest_permit(self, path, project_name):
        """Ingest a permit document into the PERMITS collection."""
        return self._ingest(
            path,
            collection=Collection.PERMITS,
            document_type=DocumentType.PERMIT_APPLICATION,
            project_name=project_name,
        )

    def ingest_reference(self, path, document_type=DocumentType.CFR_TEXT):
        """Ingest a reference document into the REFERENCE collection."""
        return self._ingest(
            path,
            collection=Collection.REFERENCE,
            document_type=document_type,
            project_name="",
        )

    def _ingest(self, path, collection, document_type, project_name):
        path = Path(path)
        logger.info("Ingesting %s into %s", path, collection.value)

        pages = load_document(path)
        if not pages:
            logger.warning("No pages from %s", path)
            return 0

        chunks = chunk_document(
            pages,
            source_path=str(path),
            document_type=document_type,
            project_name=project_name,
        )
        if not chunks:
            logger.warning("No chunks from %s", path)
            return 0

        vectors = self.embeddings.encode([c.text for c in chunks])
        self.store.add(collection, chunks, vectors)
        logger.info("Added %d chunks from %s", len(chunks), path)
        return len(chunks)
