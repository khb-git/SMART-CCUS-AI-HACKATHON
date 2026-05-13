"""
Smoke tests for the RAG scaffold.

These verify the public interfaces wire together. They DON'T test
actual loading/chunking/embedding/retrieval — that's implementation work.
As real logic gets added, these tests should keep passing.
"""

from pathlib import Path

import pytest

from rag.chunker import chunk_document
from rag.embeddings import Embeddings
from rag.generator import Generator
from rag.loaders import load_document
from rag.pipeline import IngestionPipeline
from rag.prompts import SYSTEM_PROMPT, build_review_prompt, format_context
from rag.retriever import Retriever
from rag.types import (
    Chunk,
    ChunkMetadata,
    Collection,
    DocumentType,
    RetrievalResult,
)
from rag.vectorstore import VectorStore


# ----- types -----

def test_two_collections_exist():
    """The two-collection design is load-bearing."""
    assert {c.value for c in Collection} == {"permits", "reference"}


def test_chunk_rejects_empty_text():
    """Empty chunks are a bug, not a valid state."""
    meta = ChunkMetadata(
        source_document="x.pdf",
        document_type=DocumentType.PERMIT_APPLICATION,
    )
    with pytest.raises(ValueError):
        Chunk(text="   ", metadata=meta)


def test_chunk_metadata_to_dict_uses_primitive_types():
    """to_dict must produce values a vector store can serialize."""
    meta = ChunkMetadata(
        source_document="data/permits/adm_decatur/application.pdf",
        document_type=DocumentType.PERMIT_APPLICATION,
        project_name="adm_decatur",
        section_id="section_07",
        subsection_id="7.2",
    )
    d = meta.to_dict()
    assert d["document_type"] == "permit_application"
    assert d["subsection_id"] == "7.2"
    for value in d.values():
        assert isinstance(value, (str, int, float))


# ----- loaders -----

def test_load_document_rejects_unsupported_format():
    with pytest.raises(ValueError):
        load_document(Path("notes.txt"))


def test_load_pdf_rejects_missing_file():
    with pytest.raises(FileNotFoundError):
        load_document(Path("does_not_exist.pdf"))


# ----- chunker -----

def test_chunker_handles_empty_input():
    """No pages -> no chunks. Not a crash."""
    result = chunk_document(
        pages=[],
        source_path="x.pdf",
        document_type=DocumentType.PERMIT_APPLICATION,
    )
    assert result == []


# ----- vectorstore -----

def test_store_rejects_length_mismatch():
    """Different number of chunks vs embeddings is a programming bug."""
    store = VectorStore()
    meta = ChunkMetadata(source_document="x", document_type=DocumentType.CFR_TEXT)
    chunks = [Chunk(text="hello", metadata=meta)]
    with pytest.raises(ValueError):
        store.add(Collection.REFERENCE, chunks, [])


# ----- retriever -----

def test_retriever_hits_both_collections():
    """retrieve_both must return results for both collections."""
    retriever = Retriever(Embeddings(), VectorStore())
    results = retriever.retrieve_both("any query")
    assert set(results.keys()) == {Collection.PERMITS, Collection.REFERENCE}


# ----- prompts -----

def test_prompt_labels_reference_and_permit_distinctly():
    """The two-collection distinction shows up in the prompt."""
    ref_meta = ChunkMetadata(
        source_document="146.txt",
        document_type=DocumentType.CFR_TEXT,
        cfr_citation="146.82(a)",
    )
    perm_meta = ChunkMetadata(
        source_document="adm.pdf",
        document_type=DocumentType.PERMIT_APPLICATION,
        project_name="adm_decatur",
        subsection_id="7.2",
    )
    ref = [RetrievalResult(
        chunk=Chunk(text="The owner shall...", metadata=ref_meta),
        score=0.9,
        collection=Collection.REFERENCE,
    )]
    perm = [RetrievalResult(
        chunk=Chunk(text="ADM proposes 5300 psi...", metadata=perm_meta),
        score=0.85,
        collection=Collection.PERMITS,
    )]
    context = format_context(ref, perm)
    assert "REGULATORY REFERENCE" in context
    assert "PERMIT PRECEDENT" in context
    assert "146.82(a)" in context
    assert "adm_decatur" in context


def test_build_review_prompt_includes_system_and_question():
    prompt = build_review_prompt("What is the MAIP?", [], [])
    assert SYSTEM_PROMPT.strip() in prompt
    assert "What is the MAIP?" in prompt


# ----- generator -----

def test_generator_construction_is_cheap():
    """Construction must not load the model — that happens on first generate()."""
    g = Generator()
    assert g._llm is None


# ----- pipeline -----

def test_pipeline_wires_together():
    """The full pipeline can be constructed without errors."""
    pipeline = IngestionPipeline()
    assert pipeline.embeddings is not None
    assert pipeline.store is not None
