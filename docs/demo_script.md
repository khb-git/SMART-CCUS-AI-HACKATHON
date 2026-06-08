# SMART CCUS Class VI Review Assistant Demo Script

This demo script walks through the current SMART CCUS Class VI Review Assistant system.

The goal is to show that the project now supports:

```text
1. Evidence-backed question answering
2. Single-document review
3. Multi-document package review
4. Markdown report export
```

---

## 1. Demo Setup

Open two terminals from the project root.

### Terminal 1: Start FastAPI

```powershell
.venv\Scripts\Activate.ps1
python -m uvicorn api.main:app --reload
```

Confirm the API is available:

```text
http://127.0.0.1:8000/docs
```

The API should show:

```text
GET  /health
POST /ask
POST /review-document
POST /review-package
```

### Terminal 2: Start Streamlit

```powershell
.venv\Scripts\Activate.ps1
python -m streamlit run ui/app.py
```

Streamlit should open at:

```text
http://localhost:8501
```

Use these sidebar settings:

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

## 2. Opening Explanation

Suggested talking points:

```text
This project is a prototype Class VI permit review assistant for CCUS workflows.

It has three main workflows:
1. Ask Assistant
2. Review Document
3. Review Package

The Ask Assistant uses the permanent indexed corpus of EPA references and permit precedents.

The Review Document and Review Package workflows process uploaded user files temporarily. Uploaded files are not stored permanently and are not added to Chroma.
```

Emphasize the storage distinction:

```text
Permanent corpus:
EPA references and permit precedent documents

Temporary review uploads:
User-uploaded documents processed only for the request
```

---

## 3. Demo Part 1: Ask Assistant

Open the **Ask Assistant** tab.

Use this question:

```text
How do applicants monitor injection pressure and flow rate?
```

Click:

```text
Ask review assistant
```

### What to show

Point out these sections:

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

### Suggested talking points

```text
This is the evidence-backed Q&A mode.

The system routes the question, expands the query using Class VI vocabulary, retrieves from the reference and permit collections, reranks candidates, and builds an answer using the evidence.

The evidence items are shown so the reviewer can inspect where the answer came from.
```

### Good things to mention

```text
Similarity scores are retrieval similarity, not correctness probabilities.
Query expansion helps connect plain-language questions to technical Class VI terms.
Diversified retrieval prevents all results from coming from one document.
```

---

## 4. Demo Part 2: Single Document Review

Open the **Review Document** tab.

Upload a document such as:

```text
ADM_Testing_and_Monitoring_Plan.pdf
```

Use:

```text
Plan type: auto
```

or, if auto classification needs to be demonstrated manually:

```text
Plan type: testing_monitoring
```

Click:

```text
Review uploaded document
```

### What to show

Point out:

```text
Document name
Detected type
Classification confidence
Overall status
Review summary
Storage policy
Finding counts
Checklist findings
Markdown report download
```

### Suggested talking points

```text
This workflow reviews one uploaded file against a document-specific checklist.

The system first classifies the uploaded document, then loads the matching YAML checklist, then runs the gap analysis engine.

The uploaded file is processed temporarily and is not stored in the permanent corpus.
```

### Explain status labels

```text
Present:
Strong evidence was found.

Evidence found:
Relevant evidence was found, but reviewer confirmation is recommended.

Missing:
No expected evidence was found by the current rule-based engine.

Unclear:
The item could not be clearly evaluated.
```

Important note:

```text
Evidence found does not necessarily mean the document is deficient.

It may mean the information is in a table, split across pages, worded differently than expected, affected by PDF extraction noise, or partially redacted.
```

### Download the report

Click:

```text
Download Markdown review report
```

Open the downloaded file and show that it includes:

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

---

## 5. Demo Part 3: Package Review

Open the **Review Package** tab.

Upload multiple documents, for example:

```text
ADM_Testing_and_Monitoring_Plan.pdf
ADM_Injection_Well_Plugging_Plan.pdf
```

Set package name:

```text
adm_demo_package
```

Click:

```text
Review uploaded package
```

### What to show

Point out:

```text
Package name
Overall package status
Detected document types
Missing required document types
Duplicate document types
Unknown documents
Expected package document types
Per-document review summaries
Markdown package report download
```

### Suggested talking points

```text
This workflow reviews multiple uploaded files as one application package.

Each file is temporarily ingested and classified.

Known document types are reviewed against their own checklists.

The package model then identifies which required and expected document types are present or missing.
```

If only two files are uploaded, explain:

```text
The package correctly detects the uploaded document types and reports the remaining required document types as missing.

That is expected because this is only a partial package upload.
```

### Download the package report

Click:

```text
Download Markdown package review report
```

Open the downloaded file and show:

```text
Package Summary
Detected Document Types
Missing Required Document Types
Missing Expected Document Types
Duplicate Document Types
Unknown Documents
Required Package Document Types
Expected Package Document Types
Per-Document Review Summaries
Priority Findings
Storage Policy
```

---

## 6. Supported Review Document Types

The system currently supports these review checklist types:

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

Suggested talking point:

```text
The review assistant is no longer limited to Testing and Monitoring. It now has checklist coverage for the major Class VI application document types.
```

---

## 7. What Is Happening Behind the Scenes

### Ask Assistant

```text
question
→ intent routing
→ query expansion
→ Chroma retrieval
→ diversified retrieval
→ reranking
→ answer synthesis
→ evidence-backed response
```

### Review Document

```text
uploaded file
→ temporary ingestion
→ document classification
→ checklist loading
→ gap analysis
→ document report
```

### Review Package

```text
uploaded files
→ temporary ingestion per file
→ classification per file
→ checklist review per known file
→ package completeness model
→ package report
```

---

## 8. What to Emphasize During Demo

### Strong points

```text
The system has a working backend and UI.
The system supports Ask, Document Review, and Package Review.
Uploaded files are temporary and not permanently stored.
The review logic is structured and testable.
The checklists are editable YAML files.
The system exports Markdown reports.
The package workflow can identify missing required document types.
```

### Technical strengths

```text
FastAPI backend
Streamlit demo UI
Chroma vector database
section-aware ingestion
query expansion
local reranking
temporary upload handling
document classification
checklist-driven gap analysis
package-level review model
Markdown report export
unit/integration tests
```

---

## 9. Current Limitations

Be clear that the system is still a prototype.

```text
No LLM reasoning layer yet.
Review findings are rule-based.
PDF table extraction can still be noisy.
Cross-page context can still be incomplete.
Approved EPA documents may still produce Evidence found instead of Present.
Package upload supports multi-file upload, not direct folder-path ingestion.
Reports are useful but still somewhat mechanical.
```

Suggested wording:

```text
The deterministic backend is intentionally being built first. The LLM layer will come later as a polish and reasoning layer on top of structured review outputs, not as a replacement for the review pipeline.
```

---

## 10. Recommended Closing Statement

Use this to close the demo:

```text
At this stage, the project has moved from a basic RAG chatbot to a working Class VI review assistant.

It can answer evidence-backed questions, review individual documents, review multi-document packages, identify missing package components, and export reviewer-facing Markdown reports.

The next stage is to improve review quality, especially table-aware extraction, checklist-specific evidence logic, and eventually an LLM layer for clearer reviewer explanations.
```

---

## 11. Common Demo Troubleshooting

### Streamlit request fails

Check that FastAPI is running:

```powershell
python -m uvicorn api.main:app --reload
```

Check Swagger:

```text
http://127.0.0.1:8000/docs
```

### Ask Assistant returns no results

Make sure Chroma has been built:

```powershell
python -m rag.index_chunks --chunked-dir data/chunked --collection auto --persist-directory chroma_data --batch-size 32
```

Confirm Streamlit sidebar uses:

```text
persist_directory = chroma_data
```

### Review Document does not classify correctly

Try selecting the plan type manually.

Then later improve:

```text
review/document_classifier.py
```

### Review Package reports many missing documents

This is expected if only a few documents were uploaded.

The package model compares uploaded files against the expected Class VI package document set.

### Uploaded files are not saved permanently

This is expected.

Review uploads are processed temporarily and are not added to:

```text
data/raw_docs/
data/chunked/
chroma_data/
```

---

## 12. Files Teammates Should Know

```text
api/main.py
FastAPI endpoints

ui/app.py
Streamlit tabs and layout

ui/api_client.py
Streamlit-to-API request helpers

review/checklists/*.yaml
Checklist definitions

review/document_classifier.py
Document type classification rules

review/gap_analysis.py
Checklist finding logic

review/package_review.py
Package-level completeness logic

review/report_export.py
Markdown report builders

review/temp_ingestion.py
Temporary upload processing

rag/ask.py
Ask Assistant workflow

rag/query_expansion.py
Class VI query expansion

rag/retriever.py
Retrieval logic

rag/reranker.py
Local reranking
```

---

## 13. Suggested Demo Order

Recommended live demo order:

```text
1. Show README overview
2. Start FastAPI
3. Start Streamlit
4. Ask Assistant question
5. Review one document
6. Download single-document report
7. Review package with multiple files
8. Download package report
9. Explain current limitations
10. Explain next development steps
```