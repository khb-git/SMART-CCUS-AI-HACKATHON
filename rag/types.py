"""Backward-compatible import shim for RAG shared types.

The canonical module is `rag.rag_types`. This file preserves older imports
such as `from rag.types import Chunk` used by tests and legacy modules.
"""

from rag.rag_types import (
    Chunk,
    ChunkMetadata,
    Collection,
    DocumentType,
    RetrievalResult,
)

__all__ = [
    "Chunk",
    "ChunkMetadata",
    "Collection",
    "DocumentType",
    "RetrievalResult",
]