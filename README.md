# SMART CCUS Class VI Review Assistant

Penn State NittCarbAI — SMART CCUS AI Hackathon

## Overview

SMART CCUS Class VI Review Assistant is a prototype reviewer-support tool for Underground Injection Control Class VI carbon storage permit applications.

The system helps reviewers inspect uploaded Class VI application materials, compare them against deterministic checklist logic, locate supporting evidence, identify missing or unclear items, map findings to regulatory citations, and export reviewer-ready reports.

The core architecture is:

```text
Backend decides.
Reviewer confirms.
LLM explains.
```

The deterministic backend owns checklist status, evidence detection, confidence labels, regulatory citations, reviewer action items, and export structure. Human reviewers confirm or revise the system’s findings. The LLM layer is intentionally reserved for later narrative explanation and should not override backend findings.

---

## Current Demo Focus

The strongest current workflow is:

```text
Review Package
```

Use the **Review Package** tab for the main demo. It supports multi-document Class VI package review with checklist rows, evidence locations, citations, reviewer confirmations, notes, JSON reviewer-state export/import, Markdown reports, final review packets, full checklist CSV export, and deficiency CSV export.

The **Ask Assistant** tab is present, but it requires a populated RAG index before it should be used for evidence-backed Q&A. If no RAG index has been built, the Ask Assistant may return empty or incomplete results.

---

## What the System Does

The application has three Streamlit workflows.

### 1. Ask Assistant

Retrieval-augmented Q&A over an indexed corpus of reference documents and permit precedents.

Current status:

```text
Available in the UI
Requires a populated RAG index
Not the main demo workflow yet
```

Use this tab only after building and validating the local RAG index.

### 2. Review Document

Temporary review of one uploaded PDF, DOCX, or XLSX document.

The system:

```text
ingests the uploaded file temporarily
classifies the document type
loads the matching checklist
runs deterministic gap analysis
returns findings with statuses, confidence labels, and excerpts
exports a Markdown document review report
```

Uploaded review documents are processed temporarily and are not added to the permanent vector database.

### 3. Review Package

Temporary review of multiple uploaded Class VI documents as one application package.

The system:

```text
classifies each uploaded document
runs checklist review for detected document types
identifies detected, missing, duplicate, unknown, and supporting documents
creates package-level metrics
creates reviewer action items
creates EPA-style completeness checklist rows
adds regulatory citations
adds evidence locations where available
supports reviewer confirmations and reviewer notes
exports Markdown, CSV, JSON, and final packet outputs
```

This is the recommended demo path.

---

## Reviewer-Facing Outputs

The Review Package workflow currently supports:

```text
Package summary
Package coverage summary
Package review metrics
Reviewer action items
Completeness checklist review
Regulatory citation mapping
Evidence locations
Cross-document related evidence
Reviewer confirmations
Reviewer notes
Reviewer confirmation summary
Reviewer state JSON export/import
Markdown package review report
Final regulator-style review packet
Full completeness checklist CSV
Focused deficiency CSV
Package coverage evidence table
Per-document review summaries
```

---

## Example Package Review Results

A successful package review may produce outputs such as:

```text
Detected document types: 9
Missing required document types: 0
Checklist rows: 95
Missing rows: 12
Required missing rows: 7
Page-located evidence: 87%
Resolved: 87%
```

These numbers will vary depending on the uploaded application package and checklist evidence.

---

## Supported Review File Types

Uploaded review files can be:

```text
.pdf
.docx
.xlsx
```

---

## Supported Class VI Plan Types

The review engine currently supports these internal `plan_type` values:

```text
project_narrative
site_geologic_characterization
aor_corrective_action
financial_responsibility
well_construction
pre_operational_testing
site_operating
testing_monitoring
injection_well_plugging
pisc_site_closure
emergency_remedial_response
```

These are backed by YAML checklist files in:

```text
review/checklists/
```

---

## Checklist Inventory

The deterministic review system currently includes:

```text
11 checklist files
105 checklist review items
```

Checklist inventory is documented in:

```text
docs/checklist_inventory.md
```

To regenerate the checklist inventory after checklist changes:

```powershell
python scripts/export_checklist_inventory.py
```

---

## Architecture

### Deterministic Review Engine

```text
review/
  checklists/                  YAML Class VI checklist definitions
  types.py                     Review dataclasses and enums
  schema.py                    Checklist loading and validation
  document_classifier.py       Rule-based document type classification
  gap_analysis.py              Checklist evidence matching and finding generation
  package_review.py            Multi-document package review orchestration
  regulatory_citations.py      Plan-level and item-level CFR citation mapping
  report_export.py             Markdown report, checklist, deficiency, and packet exports
  temp_ingestion.py            Temporary upload ingestion wrapper
```

### Ingestion

```text
ingestion/
  main.py                      PDF/DOCX/XLSX extraction and temporary review chunks
```

### API

```text
api/
  main.py                      FastAPI backend
```

Main endpoints:

```text
GET  /health
POST /ask
POST /review-document
POST /review-package
GET  /demo/maip-package
GET  /demo/maip-package/report
GET  /demo/maip-package/final-packet
```

### Streamlit UI

```text
ui/
  app.py                       Main Streamlit interface
  api_client.py                API client and export helpers
  reviewer_workflow.py         Reviewer confirmation, notes, CSV, and JSON helpers
  rag_status.py                Ask Assistant readiness messaging
```

### RAG Scaffold

```text
rag/
  ask.py
  chunker.py
  embeddings.py
  evidence.py
  generator.py
  index_chunks.py
  query_chroma.py
  query_expansion.py
  query_intent.py
  reranker.py
  retriever.py
  review_answer.py
  types.py
  vectorstore.py
```

The RAG path is intended for Ask Assistant Q&A. It should be treated as a separate workflow from the deterministic package review engine.

---

## Quick Start

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Run tests

```powershell
python -m pytest tests/
```

### 4. Start the FastAPI backend

```powershell
python -m uvicorn api.main:app --reload
```

FastAPI will run at:

```text
http://127.0.0.1:8000
```

Swagger docs:

```text
http://127.0.0.1:8000/docs
```

### 5. Start the Streamlit UI

Open a second terminal:

```powershell
python -m streamlit run ui/app.py
```

Streamlit will run at:

```text
http://localhost:8501
```

In the sidebar, use:

```text
FastAPI URL: http://127.0.0.1:8000
Chroma persist directory: chroma_data
```

---

## Recommended Demo Workflow

### Demo: Review Package

```text
1. Start FastAPI.
2. Start Streamlit.
3. Open the Review Package tab.
4. Upload multiple Class VI application documents.
5. Click Review uploaded package.
6. Show package summary and detected document types.
7. Show package review metrics.
8. Show reviewer action items.
9. Show completeness checklist rows.
10. Show regulatory citations and page locations.
11. Add reviewer confirmations and notes.
12. Download the final review packet.
13. Download the deficiency CSV.
14. Download reviewer state JSON.
```

This workflow demonstrates the strongest parts of the system: deterministic review, auditability, reviewer-in-the-loop workflow, and regulator-style exports.

For a step-by-step judge/demo runbook, see:

```text
docs/demo_readiness_checklist.md
```

---

## MAIP Demo Fixture

A deterministic MAIP demo package is available without uploaded files, RAG, or an LLM.

Run:

```powershell
python -m demo_samples.maip_demo_package
```

The same deterministic fixture is also available through FastAPI.

Start the backend:

```powershell
python -m uvicorn api.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/demo/maip-package
http://127.0.0.1:8000/demo/maip-package/report
http://127.0.0.1:8000/demo/maip-package/final-packet
```

The fixture exercises the full MAIP workflow:

```text
conservative MAIP evidence extraction
MAIP cross-reference validation
source document and page traceability
evidence audit trail metadata
Markdown package report export
final review packet export
```

The demo package includes representative in-memory document reviews for:

```text
Site Operating Plan
Site Geologic Characterization
AoR and Corrective Action Plan
Well Construction Plan
Testing and Monitoring Plan
```

The MAIP demo is intended for regression testing, judge review, and quick local demonstration of the deterministic MAIP workflow. It does not require uploaded files, vector indexing, RAG, or LLM services.

Run the demo tests with:

```powershell
python -m pytest tests/test_maip_demo_sample.py
python -m pytest tests/test_maip_demo_api.py
```

---

## Review Status Labels

Checklist findings use four main statuses.

### Present

Strong evidence was found for the checklist item.

### Evidence found

Relevant evidence was found, but reviewer confirmation is recommended.

This status is intentionally conservative. It may mean the system found potentially relevant support but still needs a human reviewer to confirm whether the item is fully satisfied.

### Missing

No expected evidence was found by the deterministic review engine.

### Unclear

The item could not be evaluated clearly from extracted text or available evidence.

---

## Reviewer Workflow

The package review UI supports reviewer confirmations:

```text
Pending review
Confirmed
Needs follow-up
Not applicable
Resolved after cross-reference
```

It also supports reviewer notes for each checklist row.

Reviewer state can be exported as JSON and imported later to restore confirmations and notes for matching checklist rows.

---

## Exports

The system currently supports:

### Markdown Package Review Report

Detailed package review output with package summary, metrics, action items, completeness checklist, coverage evidence, and per-document findings.

### Final Review Packet

A regulator-style packet that includes:

```text
Final package summary
Package review metrics
Reviewer action items
Deficiency table
Completeness checklist
Reviewer sign-off section
Reviewer confirmation summary
Reviewer confirmation export
Full package review appendix
```

### Full Completeness Checklist CSV

CSV export of all displayed checklist rows.

### Deficiency CSV

CSV export of unresolved rows only:

```text
Missing
Evidence found
Unclear
```

### Reviewer State JSON

Portable reviewer state export for restoring reviewer confirmations and notes later.

---

## Ask Assistant and RAG Status

The Ask Assistant is designed for retrieval-augmented Q&A over indexed reference documents and permit precedents.

Current boundary:

```text
Review Document and Review Package are active deterministic workflows.
Ask Assistant requires a populated local RAG index.
If no index is built, Ask Assistant results may be empty or incomplete.
```

The UI now displays a readiness notice in the Ask Assistant tab so users understand this boundary.

---

## Storage Policy

The system distinguishes between:

```text
permanent indexed corpus
temporary uploaded review documents
```

### Permanent indexed corpus

These files support RAG/Ask Assistant after indexing:

```text
EPA Class VI reference documents
EPA permit application materials
permit precedent documents
technical reference documents
```

Typical local folders:

```text
data/raw_docs/
data/chunked/
chroma_data/
```

### Temporary uploaded review documents

Files uploaded through:

```text
POST /review-document
POST /review-package
Streamlit Review Document tab
Streamlit Review Package tab
```

are processed in temporary directories.

Uploaded review files are not stored in:

```text
data/raw_docs/
data/chunked/
chroma_data/
reference collection
permits collection
```

---

## Build the Permanent RAG Corpus

This is only needed for Ask Assistant.

### 1. Scrape and download documents

```powershell
python scraper.py
```

Expected outputs:

```text
data/manifest.json
data/raw_docs/
```

### 2. Ingest documents

```powershell
python -m ingestion.main --manifest data/manifest.json --output data/chunked
```

### 3. Index chunks into Chroma

```powershell
python -m rag.index_chunks --chunked-dir data/chunked --collection auto --persist-directory chroma_data --batch-size 32
```

### 4. Test retrieval

```powershell
python -m rag.query_chroma --query "How do applicants monitor injection pressure and flow rate?" --collection permits --persist-directory chroma_data --k 5 --section-id 8 --diversified --fetch-k 30 --max-per-source 1
```

---

## Development Workflow

Create feature branches from `develop`:

```powershell
git checkout develop
git pull origin develop
git checkout -b feature/<branch-name>
```

Run tests before committing:

```powershell
python -m pytest tests/
```

Commit and push:

```powershell
git status
git add <changed-files>
git commit -m "Short descriptive message"
git push origin feature/<branch-name>
```

Open pull requests with:

```text
base: develop
compare: feature/<branch-name>
```

---

## Common Troubleshooting

### FastAPI is not running

Start the backend:

```powershell
python -m uvicorn api.main:app --reload
```

Check:

```text
http://127.0.0.1:8000/docs
```

### Streamlit cannot find the API

Confirm the sidebar has:

```text
FastAPI URL: http://127.0.0.1:8000
```

### Ask Assistant returns empty results

Ask Assistant requires a populated RAG index.

Use the Review Document and Review Package tabs for deterministic checklist review when no RAG index is available.

### Review Document fails with unsupported file type

Supported uploaded review file types are:

```text
.pdf
.docx
.xlsx
```

### Review Package does not detect the expected document type

Try:

```text
1. Check the filename.
2. Check whether the document title is present in extracted text.
3. Try manual plan_type in Review Document mode.
4. Add classifier synonyms in review/document_classifier.py.
5. Add or adjust checklist evidence terms in review/checklists/.
```

### Generated folders show in Git

Do not commit local data/vector stores.

Common local folders:

```text
data/raw_docs/
data/chunked/
chroma_data/
.pytest_cache/
.venv/
__pycache__/
```

---

## Known Limitations

The current system is still a prototype.

Known limitations:

```text
Ask Assistant depends on a populated RAG index
RAG chunking/indexing path needs continued hardening
No LLM narrative layer yet
Rule-based review can return Evidence found for documents that need human interpretation
PDF table extraction can be noisy
Cross-page context can be incomplete
Some findings depend heavily on checklist terms and anchor terms
Package upload supports multi-file upload, not direct folder-path ingestion
```

---

## Recommended Next Improvements

Likely next development areas:

```text
1. Add LLM review narrative layer over deterministic findings
2. Improve table-aware review logic
3. Implement or consolidate minimal RAG chunking
4. Add FastAPI integration tests with fixture documents
5. Improve checklist-specific evidence logic
6. Add deployment configuration
7. Add broader regression tests using real EPA documents
```

The LLM should improve explanation quality, not replace the deterministic review pipeline.

Recommended LLM input structure:

```text
checklist item
+ backend status
+ confidence
+ regulatory citation
+ file name
+ page number
+ evidence excerpt
+ reviewer confirmation
+ reviewer notes
+ recommended fix
→ LLM-generated reviewer narrative
```

---

## Team Notes

When modifying the system:

```text
Use review/checklists/*.yaml to update checklist requirements.
Use review/document_classifier.py to improve auto document classification.
Use review/gap_analysis.py to improve finding status logic.
Use review/package_review.py to improve package-level completeness logic.
Use review/regulatory_citations.py to improve citation mapping.
Use review/report_export.py to improve Markdown and packet exports.
Use ui/reviewer_workflow.py to improve reviewer confirmation, notes, JSON, and CSV workflows.
Use ui/app.py to adjust Streamlit layout.
Use api/main.py to adjust FastAPI endpoints.
```

Recommended testing pattern:

```powershell
python -m pytest tests/test_api_routes.py
python -m pytest tests/test_rag_status.py
python -m pytest tests/test_streamlit_completeness_checklist_view.py
python -m pytest tests/test_final_review_packet_export.py
python -m pytest tests/
```