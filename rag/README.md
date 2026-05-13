# RAG scaffold

Skeleton of the RAG pipeline for NittCarb AI's Class VI permit review.
Every module has its interface defined and a `# TODO` for the real work.

## Layout

```
rag/
├── types.py         shared dataclasses + Collection enum
├── loaders.py       PDF + DOCX loaders
├── chunker.py       schema-aware chunking (the important one)
├── embeddings.py    local sentence-transformers
├── vectorstore.py   Chroma, two collections (permits + reference)
├── retriever.py     picks collection + applies filters
├── prompts.py       review-specific prompt templates
├── generator.py     LLM placeholder
└── pipeline.py      load -> chunk -> embed -> store
tests/
└── test_rag.py      11 smoke tests for the public interfaces
```

## Run the tests

```bash
pytest tests/
```

You should see 11 tests pass. They exercise the interfaces, not the
real implementations (which are stubs that log warnings).

## Key design decisions

**Two collections, kept separate.** `Collection.PERMITS` holds chunks
from the seven approved permit applications. `Collection.REFERENCE`
holds chunks from 40 CFR Part 146 Subpart H and EPA guidance. A
retrieval for "what does the regulation say about casing" must never
return an applicant's casing description, and vice versa.

**Schema-aware chunking.** Chunks respect REVIEW_SCHEMA section
boundaries and carry `section_id` / `subsection_id` in metadata.
This is what makes the MAIP validation chain enforceable later — every
chunk knows which section it came from, so cross-reference queries can
filter by section.

**Everything runs locally.** Air-gapped deployment is a hard constraint.
No cloud API calls in the RAG path.

## Filling in the TODOs

Each module has TODOs marked with `# TODO`. Suggested order:

1. `loaders.py` — implement `load_pdf` against one of your permit PDFs.
2. `chunker.py` — implement `chunk_document` and `detect_sections`.
3. `embeddings.py` — wire up `SentenceTransformer`.
4. `vectorstore.py` — wire up the Chroma client.
5. `pipeline.py` — should work end-to-end once 1–4 are done.
6. `retriever.py` — already works; tests will start returning real results.
7. `generator.py` — wait for the LLM benchmark decision before filling.
