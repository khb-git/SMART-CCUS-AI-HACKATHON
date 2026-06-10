# SMART CCUS AI Hackathon

Repository for the Penn State NittCarbAI SEG Hackathon team.

This project is a prototype **Class VI permit review assistant** for CCUS workflows. It supports evidence-backed question answering, single-document review, and multi-document package review for Class VI application materials.

The system can:

```text
Ask questions over indexed EPA reference and permit precedent documents
Review one uploaded document against a document-specific checklist
Review a package of uploaded documents for completeness
Explain why package topics were credited as detected
Export single-document and package-level Markdown review reports
Display reviewer-facing package coverage evidence in Streamlit
```

---

## Current Capabilities

### 1. Ask Assistant

The Ask Assistant is a RAG-style review assistant over the permanent indexed corpus.

It supports questions such as:

```text
How do applicants monitor injection pressure and flow rate?
What does Class VI require for testing and monitoring?
Compare applicant injection pressure monitoring against EPA expectations.
How do applicants handle groundwater monitoring?
What evidence supports continuous monitoring requirements?
```

The Ask Assistant pipeline is:

```text
question
→ intent routing
→ query expansion
→ reference/permit retrieval
→ diversified retrieval
→ local reranking
→ evidence packaging
→ evidence-grounded answer synthesis
→ FastAPI /ask endpoint
→ Streamlit Ask Assistant tab
```

### 2. Single Document Review

The Review Document workflow lets a user upload one PDF/DOCX/XLSX file for temporary checklist review.

Pipeline:

```text
uploaded document
→ temporary ingestion
→ document classification
→ checklist loading
→ gap analysis
→ review findings
→ Streamlit Review Document tab
→ Markdown document review report
```

The uploaded file is processed temporarily and is not added to the permanent vector database.

### 3. Package Review

The Review Package workflow lets a user upload multiple PDF/DOCX/XLSX files from a Class VI application package.

Pipeline:

```text
uploaded package files
→ temporary ingestion per file
→ document classification per file
→ checklist review per file
→ package completeness review
→ detected/missing/duplicate/unknown document summary
→ Streamlit Review Package tab
→ Markdown package review report
```

This workflow identifies:

```text
detected package topics
missing required package topics
missing expected package topics
duplicate primary document types
unknown documents
supporting documents
per-document review summaries
priority findings
package coverage evidence
```

Package review now distinguishes between:

```text
document_type          primary identity of the uploaded document
covered_plan_types     checklist reports actually run for that document
coverage_plan_types    package completeness topics credited from filename, classification, checklist review, or text evidence
coverage_evidence      reviewer-facing explanation of why each package topic was credited
```

This distinction is important for combined documents. For example, a project narrative may also contain financial responsibility evidence. The package review can credit the financial responsibility topic while still showing the reviewer which file supplied the evidence and why the topic was credited.
```
---

## Checklist Inventory

The review system currently includes:

```text
11 checklist files
105 checklist review items
```

The checklist inventory is generated from the YAML checklist files and stored in:

```text
docs/checklist_inventory.md
```

Current checklist coverage includes:

| Plan type | Item count |
| --- | ---: |
| `project_narrative` | 13 |
| `aor_corrective_action` | 10 |
| `financial_responsibility` | 10 |
| `well_construction` | 10 |
| `pre_operational_testing` | 5 |
| `testing_monitoring` | 17 |
| `injection_well_plugging` | 10 |
| `pisc_site_closure` | 10 |
| `emergency_remedial_response` | 10 |
| `site_geologic_characterization` | 5 |
| `site_operating` | 5 |

To regenerate the inventory after checklist changes:

```powershell
python scripts/export_checklist_inventory.py
```

---

## Package Coverage Evidence

Package review includes a reviewer-facing coverage evidence layer.

For each credited package topic, the system can show:

```text
package topic
document name
primary document type
evidence source
matched evidence terms
reviewer note
```

Evidence sources may include:

```text
primary_document_type
checklist_review
filename
classifier
text_evidence
```

The evidence table is available in:

```text
/review-package JSON response
Markdown package review export
Streamlit Review Package tab
```

Text evidence is intended to support reviewer triage. It is not treated as an automatic final compliance determination.

---

## Important Storage Policy

The system distinguishes between the **permanent indexed corpus** and **temporary uploaded review documents**.

### Permanent indexed corpus

These files are scraped/downloaded, chunked, and indexed into Chroma:

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

Uploaded review files are **not** stored in:

```text
data/raw_docs/
data/chunked/
chroma_data/
reference collection
permits collection
```

The review responses include a storage policy message confirming that uploaded review files are processed temporarily and are not retained in permanent data folders or Chroma collections.

---

## Current System Overview

The full system has three connected workflows.

### Permanent RAG Corpus Workflow

```text
scrape/download
→ manifest with local paths
→ PDF/DOCX/XLSX ingestion
→ text/table extraction
→ section-aware chunking
→ schema metadata tagging
→ Chroma vector indexing
→ query intent routing
→ query expansion
→ diversified retrieval
→ local reranking
→ evidence packaging
→ evidence-grounded answer synthesis
```

### Single-Document Review Workflow

```text
uploaded PDF/DOCX/XLSX
→ temporary file handling
→ temporary text/table/chunk extraction
→ rule-based document classification
→ checklist selection
→ rule-based gap analysis
→ finding statuses
→ Markdown report export
```

### Package Review Workflow

```text
multiple uploaded PDF/DOCX/XLSX files
→ temporary ingestion for each file
→ classification for each file
→ checklist review for each known document
→ package-level completeness check
→ missing/duplicate/unknown document detection
→ package coverage evidence routing
→ Streamlit package coverage evidence display
→ package Markdown report export
```

---

## Repository Structure

```text
api/
  main.py                         FastAPI backend:
                                  /health
                                  /ask
                                  /review-document
                                  /review-package

ingestion/
  main.py                         PDF/DOCX/XLSX ingestion and chunking

rag/
  ask.py                          End-to-end CLI ask workflow
  evidence.py                     Evidence packaging
  index_chunks.py                 Chroma indexing workflow
  query_chroma.py                 Retrieval smoke-test CLI
  query_expansion.py              Class VI query expansion
  query_intent.py                 Query intent routing
  reranker.py                     Lightweight local reranking
  retriever.py                    Schema-aware retrieval
  review_answer.py                Structured review answer builder
  answer_synthesis.py             Evidence-grounded answer synthesis
  vectorstore.py                  Chroma wrapper
  embeddings.py                   Embedding wrapper
  types.py                        Shared dataclasses/types

review/
  checklists/                     YAML review checklists by document type
  coverage_evidence_display.py    UI formatting for package coverage evidence
  document_classifier.py          Rule-based document type classifier
  gap_analysis.py                 Checklist gap analysis engine
  package_review.py               Multi-document package review model
  report_export.py                Markdown report export helpers
  schema.py                       Checklist loading/parsing
  temp_ingestion.py               Temporary upload ingestion
  types.py                        Review dataclasses/enums

ui/
  app.py                          Streamlit UI:
                                  Ask Assistant
                                  Review Document
                                  Review Package
  api_client.py                   Streamlit API client helpers

docs/
  checklist_inventory.md          Generated checklist inventory
  project_status.md               Current project status summary

tests/
  test_*.py                       Unit/integration tests

scraper.py                        Scraper entry point
requirements.txt                  Python dependencies
README.md                         Project documentation
```

---

## Setup

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

### 3. Confirm tests pass

```powershell
python -m pytest tests/
```

---

## Environment Variables

The ingestion workflow can use `.env` values, but CLI flags can also be used directly.

Example `.env`:

```env
PATH_TO_RAW_DATA_DIR=data/raw_docs
PATH_TO_CHUNKED_DATA_DIR=data/chunked
PATH_TO_MANIFEST=data/manifest.json
```

Local/generated data folders are intentionally not committed.

---

## Build the Permanent Corpus

The permanent corpus supports the Ask Assistant. This is separate from temporary uploaded review documents.

### Step 1: Scrape and Download Documents

Run the scraper/downloader workflow:

```powershell
python scraper.py
```

Expected outputs:

```text
data/manifest.json
data/raw_docs/
```

The manifest should include a `local_path` field for each downloaded file.

### Step 2: Ingest Documents

Run ingestion from the manifest:

```powershell
python -m ingestion.main --manifest data/manifest.json --output data/chunked
```

Expected successful output should look similar to:

```json
{
  "processed": 112,
  "skipped_missing_local_path": 0,
  "skipped_missing_file": 0,
  "skipped_unsupported_type": 0,
  "failed": 0
}
```

The ingestion step handles:

```text
PDF text
PDF tables
DOCX text
DOCX tables
XLSX tables
section-aware chunk context
schema-aware metadata
```

### Step 3: Index Chunks into Chroma

Index the chunked data into the local Chroma vector database:

```powershell
python -m rag.index_chunks --chunked-dir data/chunked --collection auto --persist-directory chroma_data --batch-size 32
```

The `--collection auto` option routes chunks into:

```text
reference
permits
```

based on document metadata.

---

## Retrieval and Ask Assistant

### Test Retrieval from the CLI

Run a direct retrieval smoke test:

```powershell
python -m rag.query_chroma --query "How do applicants monitor injection pressure and flow rate?" --collection permits --persist-directory chroma_data --k 5 --section-id 8 --diversified --fetch-k 30 --max-per-source 1
```

Useful comparison flags:

```powershell
--no-query-expansion
--no-reranking
```

Example:

```powershell
python -m rag.query_chroma --query "How do applicants monitor injection pressure and flow rate?" --collection permits --persist-directory chroma_data --k 5 --section-id 8 --diversified --fetch-k 30 --max-per-source 1 --no-query-expansion
```

### Run the Ask CLI

The ask CLI runs the full assistant workflow:

```powershell
python -m rag.ask --query "How do applicants monitor injection pressure and flow rate?" --persist-directory chroma_data --section-id 8
```

This performs:

```text
intent routing
query expansion
retrieval
reranking
evidence packaging
answer synthesis
formatted answer output
```

Useful flags:

```powershell
--intent auto
--intent regulatory_requirement
--intent permit_precedent
--intent cross_check
--intent general_review
--no-query-expansion
--no-reranking
```

Example cross-check:

```powershell
python -m rag.ask --query "Compare applicant injection pressure monitoring against EPA expectations." --persist-directory chroma_data --section-id 8 --intent cross_check
```

---

## Run the FastAPI Backend

Start the API server:

```powershell
python -m uvicorn api.main:app --reload
```

The API should be available at:

```text
http://127.0.0.1:8000
```

Swagger docs:

```text
http://127.0.0.1:8000/docs
```

### Available API Endpoints

```text
GET  /health
POST /ask
POST /review-document
POST /review-package
```

---

## API Endpoint: `/ask`

The `/ask` endpoint answers questions using the permanent indexed corpus.

Example request body:

```json
{
  "query": "How do applicants monitor injection pressure and flow rate?",
  "persist_directory": "chroma_data",
  "section_id": "8",
  "intent": "auto",
  "k_reference": 3,
  "k_permits": 5,
  "fetch_k": 30,
  "max_per_source": 1,
  "expand_retrieval_query": true,
  "use_reranking": true
}
```

Expected response includes:

```text
answer
reviewer_interpretation
potential_follow_up
evidence_summary
evidence_items
```

---

## API Endpoint: `/review-document`

The `/review-document` endpoint reviews one uploaded document temporarily.

Input:

```text
file: PDF/DOCX/XLSX
plan_type: auto or a supported plan type
chunk_size: default 1000
chunk_overlap: default 100
```

Example usage through Swagger:

```text
POST /review-document
file = ADM_Testing_and_Monitoring_Plan.pdf
plan_type = auto
```

or manually:

```text
plan_type = testing_monitoring
```

Expected response includes:

```text
document_name
document_type
classification_confidence
classification
report
storage_policy
```

The `report` includes:

```text
overall_status
summary
findings
```

---

## API Endpoint: `/review-package`

The `/review-package` endpoint reviews multiple uploaded documents as one temporary package.

Input:

```text
files: multiple PDF/DOCX/XLSX files
package_name: default uploaded_package
chunk_size: default 1000
chunk_overlap: default 100
```

Example usage through Swagger:

```text
POST /review-package
files = multiple Class VI documents
package_name = adm_package
```

Expected response includes:

```text
package_name
report
storage_policy
```

The package `report` includes:

```text
overall_status
summary
expected_plan_types
required_plan_types
detected_plan_types
missing_required_plan_types
missing_expected_plan_types
duplicate_plan_types
unknown_documents
supporting_documents
document_reviews
coverage_evidence
```
`coverage_evidence` explains why package topics were credited as detected. It includes the credited topic, source document, primary document type, evidence source, matched terms, and reviewer note.
---

## Run the Streamlit UI

Keep the FastAPI server running in one terminal:

```powershell
python -m uvicorn api.main:app --reload
```

Open a second terminal and run:

```powershell
python -m streamlit run ui/app.py
```

Streamlit should open at:

```text
http://localhost:8501
```

In the sidebar, use:

```text
FastAPI URL: http://127.0.0.1:8000
Chroma persist directory: chroma_data
Section ID: 8
Intent: auto
Reference evidence count: 3
Permit evidence count: 5
Raw candidates before diversification: 30
Max evidence items per source: 1
Use query expansion: checked
Use local reranking: checked
```

---

## Streamlit Tab: Ask Assistant

Use this tab to ask evidence-backed questions over the permanent corpus.

Example question:

```text
How do applicants monitor injection pressure and flow rate?
```

Expected UI sections:

```text
Answer
Reviewer interpretation
Potential follow-up
Evidence summary
Evidence items
Source document links
Similarity scores
Excerpts
```

---

## Streamlit Tab: Review Document

Use this tab to upload and review one document.

Steps:

```text
1. Open Review Document tab
2. Upload PDF/DOCX/XLSX
3. Select plan_type = auto or a manual checklist type
4. Click Review uploaded document
5. Inspect classification and checklist findings
6. Download Markdown review report
```

Expected UI sections:

```text
Document name
Detected type
Classification confidence
Overall status
Summary
Storage policy
Finding counts
Checklist findings
Matched terms
Supporting excerpts
Recommended fixes
Markdown report download button
```

---

## Streamlit Tab: Review Package

Use this tab to upload and review multiple documents as a package.

Steps:

```text
1. Open Review Package tab
2. Upload multiple PDF/DOCX/XLSX files
3. Enter package name
4. Click Review uploaded package
5. Inspect package-level completeness
6. Inspect per-document summaries
7. Download Markdown package review report
```

Expected UI sections:

```text
Package name
Overall package status
Detected package topics
Missing required package topics
Duplicate primary document types
Unknown documents
Supporting documents
Package Coverage Evidence table
Expected package document types
Per-document review summaries
Optional per-document findings
Markdown package report download button
```

---

## Supported Review Document Types

The review assistant currently supports these internal `plan_type` values:

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

These correspond to checklist YAML files under:

```text
review/checklists/
```

Supported checklist files include:

```text
aor_corrective_action.yaml
emergency_remedial_response.yaml
financial_responsibility.yaml
injection_well_plugging.yaml
pisc_site_closure.yaml
pre_operational_testing.yaml
project_narrative.yaml
site_geologic_characterization.yaml
site_operating.yaml
testing_monitoring.yaml
well_construction.yaml
```

---

## Review Status Labels

Checklist findings use these statuses:

```text
Present
Evidence found
Missing
Unclear
```

### Present

Strong evidence was found for the checklist item.

### Evidence found

Relevant evidence was found, but reviewer confirmation is recommended.

This label is intentionally conservative. It does not necessarily mean the document is deficient. It may mean the rule-based reviewer found limited evidence because the relevant information is:

```text
in a table
split across pages
worded differently than expected terms
affected by PDF extraction noise
partially redacted
```

### Missing

No expected evidence was found by the current rule-based review engine.

### Unclear

The checklist item could not be evaluated clearly.

---

## Package-Level Status Labels

Package reports may use statuses such as:

```text
package_review_ready
mostly_complete
incomplete
needs_revision
needs_review
missing_required_documents
```

The most common package-level issue is:

```text
missing_required_documents
```

This means one or more required package document types were not detected among the uploaded files.

---

## Markdown Reports

### Single-Document Markdown Report

The single-document report includes:

```text
Document Summary
Review Summary
Finding Counts
Classification Details
Storage Policy
Checklist Findings
Matched Terms
Supporting Excerpts
Recommended Fixes
```

Default filename format:

```text
<document_name>_review_report.md
```

### Package Markdown Report

The package report includes:

```text
Package Summary
Reviewer Priority Summary
Detected Document Types
Missing Required Document Types
Missing Expected Document Types
Duplicate Primary Document Types
Unknown Documents
Supporting Documents
Required Package Document Types
Expected Package Document Types
Storage Policy
Document Review Overview
Package Coverage Evidence
Detailed Per-Document Review Summaries
Priority Findings
```

Default filename format:

```text
<package_name>_package_review_report.md
```

---

## Current Retrieval Features

### Query Intent Routing

The system classifies questions into:

```text
regulatory_requirement
permit_precedent
cross_check
general_review
```

Examples:

```text
What does Class VI require for testing and monitoring?
→ reference collection

How do applicants monitor injection pressure and flow rate?
→ permits collection

Compare applicant injection pressure monitoring against EPA expectations.
→ reference + permits
```

### Query Expansion

Natural-language questions are expanded with Class VI vocabulary.

Example:

```text
flow rate
→ injection rate, mass flow rate, mass flowmeter, Coriolis meter, orifice meter

pressure
→ wellhead pressure, annulus pressure, downhole pressure, pressure transducer

monitoring
→ continuous recording devices, SCADA, operational parameters
```

The original user question is still displayed. The expanded query is only used for retrieval.

### Diversified Retrieval

Results are diversified by source document to avoid returning too many chunks from the same PDF.

Recommended demo setting:

```text
max_per_source = 1
```

### Local Reranking

A lightweight local reranker compares retrieved candidates against the original user question using lexical overlap and Class VI technical term boosts.

Reranking may not always increase the displayed similarity score, because displayed scores remain Chroma similarity scores. Reranking is meant to improve result ordering and answer relevance.

### Similarity Scores

Similarity scores are retrieval similarity values, not correctness probabilities.

Example:

```text
Similarity score: 0.7851
```

This means the chunk was highly similar to the retrieval query. It does not mean the answer is 78.51% correct.

---

## Recommended Demo Questions

### Permit precedent

```text
How do applicants monitor injection pressure and flow rate?
```

```text
How do applicants monitor groundwater during injection?
```

```text
How do applicants track plume and pressure front movement?
```

### Regulatory/reference

```text
What does Class VI require for testing and monitoring?
```

```text
What does EPA guidance say about mechanical integrity testing?
```

### Cross-check

```text
Compare applicant injection pressure monitoring against EPA expectations.
```

```text
Evaluate whether the applicant testing and monitoring plan is adequate.
```

```text
What gaps should a reviewer look for in a Testing and Monitoring Plan?
```

---

## Recommended Demo Workflows

### Demo 1: Ask Assistant

```text
1. Start FastAPI
2. Start Streamlit
3. Open Ask Assistant tab
4. Ask: How do applicants monitor injection pressure and flow rate?
5. Show answer, reviewer interpretation, and evidence items
```

### Demo 2: Single Document Review

```text
1. Open Review Document tab
2. Upload a Testing and Monitoring Plan PDF
3. Use plan_type = auto
4. Run review
5. Show classification, Evidence found findings, and report export
```

### Demo 3: Package Review

```text
1. Open Review Package tab
2. Upload multiple Class VI application documents
3. Run package review
4. Show detected document types
5. Show missing required document types
6. Show per-document review summaries
7. Download package Markdown report
```

---

## Development Workflow

Use feature branches:

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

Open a PR with:

```text
base: develop
compare: feature/<branch-name>
```

---

## Common Troubleshooting

### FastAPI is not running

If Streamlit shows a backend request error, make sure this command is running in another terminal:

```powershell
python -m uvicorn api.main:app --reload
```

Check:

```text
http://127.0.0.1:8000/docs
```

### Streamlit cannot find the API

Confirm the UI sidebar has:

```text
FastAPI URL: http://127.0.0.1:8000
```

### Chroma directory not found or no Ask Assistant results

Make sure chunks were indexed:

```powershell
python -m rag.index_chunks --chunked-dir data/chunked --collection auto --persist-directory chroma_data --batch-size 32
```

Then use:

```text
persist_directory: chroma_data
```

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
1. Check the filename
2. Check whether the document title is present in extracted text
3. Try manual plan_type in Review Document mode
4. Add classifier synonyms in review/document_classifier.py
5. Add or adjust checklist evidence terms in review/checklists/
```

### Generated folders showing in Git

Do not commit local data/vector stores.

Common local folders:

```text
data/raw_docs/
data/chunked/
data/chunked_section_test/
chroma_data/
chroma_data_section_test/
.pytest_cache/
.venv/
__pycache__/
```

### Hugging Face warning on Windows

You may see:

```text
Warning: You are sending unauthenticated requests to the HF Hub.
```

or symlink/cache warnings. These are not blockers for local development. A Hugging Face token can improve download limits, but the system can run without one.

---

## Current Status

The project currently has:

```text
working ingestion
working vector indexing
working retrieval
working Ask CLI
working FastAPI backend
working Streamlit UI
working Ask Assistant tab
working Review Document tab
working Review Package tab
working single-document Markdown export
working package Markdown export
temporary upload handling
multiple review checklists
automatic document classification
package-level completeness review
105 checklist review items
package coverage evidence routing
package coverage evidence Markdown export
package coverage evidence Streamlit display
passing tests
```

---

## Known Limitations

The current system is still a prototype.

Current limitations:

```text
No LLM reasoning layer yet
Rule-based review can still return Evidence found for approved documents
PDF table extraction can still be noisy
Cross-page context can still be incomplete
Some findings depend heavily on checklist terms and anchor terms
Package upload supports multi-file upload, not direct folder-path ingestion
Review reports are useful but still mechanical
```

`Evidence found` should be treated as:

```text
Relevant evidence was detected, but a reviewer should confirm whether the document fully satisfies the checklist item.
```

---

## Recommended Next Improvements

Likely next development areas:

```text
1. Create final demo walkthrough and sample package report
2. Improve checklist-specific evidence logic
3. Improve table serialization and table-aware review
4. Add package-level report polish
5. Add LLM review-polish layer
6. Add LLM follow-up chat over uploaded document/package results
7. Add deployment configuration
8. Add broader regression test suites using real EPA documents
```

The LLM should be added after the deterministic backend remains stable. The recommended design is:

```text
checklist item
+ status
+ matched terms
+ supporting excerpts
+ recommended fix
+ reference evidence
→ LLM-generated reviewer explanation
```

The LLM should improve explanation quality, not replace the structured review pipeline.

---

## Team Notes

When modifying the system:

```text
Use review/checklists/*.yaml to update checklist requirements.
Use review/document_classifier.py to improve auto document classification.
Use review/gap_analysis.py to improve finding status logic.
Use review/package_review.py to improve package-level completeness logic.
Use review/report_export.py to improve Markdown reports.
Use ui/app.py to adjust Streamlit layout.
Use api/main.py to adjust FastAPI endpoints.
```

Recommended testing pattern:

```powershell
python -m pytest tests/test_document_classifier_evaluation.py
python -m pytest tests/test_review_package_model.py
python -m pytest tests/test_review_package_api.py
python -m pytest tests/test_streamlit_api_client.py
python -m pytest tests/
```