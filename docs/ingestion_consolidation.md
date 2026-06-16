Ingestion Consolidation Plan
Purpose
This document captures the planned consolidation between the working review-ingestion path and the RAG chunking/indexing path.
The current deterministic review workflows are functional and should not be disrupted before the demo. The purpose of this plan is to prevent future drift when the RAG path is implemented or hardened.
---
Current State
The repository currently has multiple ingestion-related paths.
1. Review upload ingestion
Used by:
```text
Review Document
Review Package
POST /review-document
POST /review-package
```
Main files:
```text
review/temp_ingestion.py
ingestion/main.py
```
This path is currently active and supports temporary PDF, DOCX, and XLSX review workflows.
It powers:
```text
document classification
checklist gap analysis
package review
evidence locations
Markdown exports
CSV exports
final review packet exports
```
2. Permanent corpus ingestion
Used for preparing a local corpus for retrieval and indexing.
Main files:
```text
ingestion/main.py
rag/index_chunks.py
```
This path supports the future Ask Assistant workflow once a permanent corpus is ingested and indexed.
3. RAG chunking scaffold
Used by the planned RAG pipeline.
Main files:
```text
rag/chunker.py
rag/types.py
rag/pipeline.py
```
This path is not the current review-engine path. It should be implemented carefully so it does not duplicate or drift away from the working ingestion behavior.
---
Problem
There are currently parallel concepts that need to converge over time.
Parallel ingestion paths
```text
review/temp_ingestion.py
ingestion/main.py
rag/chunker.py
rag/pipeline.py
```
Parallel document/chunk representations
```text
review/temp_ingestion.py / ingestion/main.py review-oriented document objects
rag/types.py Chunk and ChunkMetadata
```
This is manageable while the RAG path is scaffolded, but it can become risky once `rag/chunker.chunk_document()` is fully implemented.
Potential risks include:
```text
different page-number handling
different section-heading detection
different table serialization behavior
different metadata field names
different chunk size or overlap behavior
different document type handling
broken cross-document evidence references
broken retrieval filters
```
---
Guiding Principle
The project should have one source of truth for document extraction and section-aware chunking.
The long-term target is:
```text
One extraction path.
One section detection strategy.
One chunk metadata contract.
Different consumers can adapt from the same canonical representation.
```
---
Proposed Target Architecture
Step 1: Keep the working review ingestion path stable
Do not break:
```text
Review Document
Review Package
temporary upload handling
checklist review
package review
exports
```
The deterministic review engine is the current product core.
---
Step 2: Define a canonical chunk contract
Use `rag/types.py` as the likely long-term canonical chunk representation because it already defines retrieval-oriented chunk metadata.
The canonical chunk should preserve:
```text
chunk text
source path
source filename
document type
collection
project name
page number
chunk index
section id
subsection id
section heading
content type
table metadata where available
```
---
Step 3: Reuse section-detection behavior from `ingestion/main.py`
When implementing or hardening `rag/chunker.chunk_document()`, do not create a separate section-heading strategy from scratch.
Instead:
```text
reuse extraction and section-heading behavior from ingestion/main.py
or move shared section detection into a common utility module
```
Potential future shared module:
```text
ingestion/section_detection.py
```
or:
```text
review/text_utils.py
```
The exact location can be decided during implementation.
---
Step 4: Adapt review ingestion and RAG ingestion from the same source
The future flow should look like:
```text
PDF/DOCX/XLSX
→ shared extraction
→ shared section detection
→ canonical chunks
→ review adapter or RAG adapter
```
The review adapter can prepare temporary review documents.
The RAG adapter can prepare persistent Chroma-ready chunks.
---
What Not To Do
Avoid this:
```text
Implement a completely separate chunker in rag/chunker.py
Copy/paste section detection logic into multiple places
Create new metadata keys without mapping them to existing review/export fields
Break temporary upload review while improving RAG
Treat RAG chunking as required for Review Package
```
The Review Package workflow does not require the RAG chunker.
---
Recommended Future Branches
1. `feature/define-canonical-chunk-contract`
Clarify the fields required for a canonical chunk and add tests around metadata completeness.
2. `feature/extract-shared-section-detection`
Move shared section-heading detection into one importable module.
3. `feature/implement-minimal-rag-chunking`
Implement `rag/chunker.chunk_document()` using the shared extraction/section strategy.
4. `feature/consolidate-review-and-rag-ingestion`
Refactor review ingestion and RAG ingestion to adapt from one canonical representation.
---
Acceptance Criteria for Future Consolidation
A future consolidation should preserve:
```text
all existing Review Document tests
all existing Review Package tests
page-number evidence locations
section-heading metadata
table extraction behavior
CSV exports
Markdown exports
final review packet exports
Ask Assistant retrieval metadata
```
A future consolidation should add tests proving that:
```text
review ingestion and RAG ingestion preserve page numbers consistently
section headings are detected consistently
table chunks preserve useful metadata
RAG chunks can be filtered by section id
review evidence locations still map back to source files and pages
```
---
Current Decision
For the hackathon demo, do not refactor ingestion yet.
Use this path:
```text
Review Package for the main demo.
Ask Assistant only after a RAG index is built and validated.
```
The ingestion consolidation work should happen after the demo-critical review workflow remains stable.