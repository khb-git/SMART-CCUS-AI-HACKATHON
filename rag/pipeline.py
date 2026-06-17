"""
Ingestion pipeline: load -> chunk -> embed -> store.

Runs offline, once per document. Separate from the online retrieval/
generation path because the two have different performance profiles.
"""

# Import modules
import logging
from pathlib import Path

from rag.chunker import chunk_document
from rag.embeddings import Embeddings
from rag.loaders import load_document
from rag.rag_types import Collection, DocumentType
from rag.vectorstore import VectorStore

from ingestion.main import annotate_documents_with_section_context
from ingestion.main import build_review_metadata
from ingestion.main import add_section_context_to_chunks

logger = logging.getLogger(__name__)

# Ingestion pipeline implementation
class IngestionPipeline:
    """Load -> chunk -> embed -> store, one document at a time."""

    # Initialize the ingestion pipeline with optional embeddings and store.
    def __init__(self, embeddings=None, store=None):
        self.embeddings = embeddings or Embeddings()
        self.store = store or VectorStore()

    # Ingest a permit document
    def ingest_permit(self, path, project_name):
        """Ingest a permit document into the PERMITS collection."""
        return self._ingest(
            path,
            collection=Collection.PERMITS,
            document_type=DocumentType.PERMIT_APPLICATION,
            project_name=project_name,
        )

    # Ingest a reference document
    def ingest_reference(self, path, document_type=DocumentType.CFR_TEXT):
        """Ingest a reference document into the REFERENCE collection."""
        return self._ingest(
            path,
            collection=Collection.REFERENCE,
            document_type=document_type,
            project_name="",
        )

    # Ingest a document into the specified collection
    def _ingest(self, path, collection, document_type, project_name):
        path = Path(path)
        logger.info("Ingesting %s into %s", path, collection.value)

        pages = load_document(path)
        pages = annotate_documents_with_section_context(pages)
        if not pages:
            logger.warning("No pages from %s", path)
            return 0
        
        chunks = chunk_document(
            pages,
            source_path=str(path),
            document_type=document_type,
            project_name=project_name,
        )
        chunks = add_section_context_to_chunks(chunks)
        for chunk in chunks:
            chunk.metadata.update(build_review_metadata(path))

        if not chunks:
            logger.warning("No chunks from %s", path)
            return 0

        vectors = self.embeddings.encode([c.text for c in chunks])
        self.store.add(collection, chunks, vectors)
        logger.info("Added %d chunks from %s", len(chunks), path)
        return len(chunks)
