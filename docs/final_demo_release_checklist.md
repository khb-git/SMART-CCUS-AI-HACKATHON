# Final Demo Release Checklist and Judge Runbook

Welcome to the SMART CCUS Class VI Review Assistant demo.

This page shows you how to run the project locally, what to look for during the demo, and how to interpret the system outputs.

The project is designed to support Underground Injection Control Class VI carbon storage permit-package review. It does not approve permits, replace reviewers, or make final regulatory determinations. It organizes review evidence, checklist findings, regulatory citations, reviewer actions, and exportable reports so a qualified reviewer can evaluate the package more efficiently.

---

## Core Architecture

The architecture is:

```text
Backend decides.
Retriever finds.
Reviewer confirms.
LLM explains.
```

Here is what that means:

```text
Backend decides checklist status, confidence, citations, and export structure.
Retriever finds supporting source evidence and page-located excerpts.
Reviewer confirms, revises, or rejects the finding.
LLM explains deterministic findings in reviewer-friendly language.
```

The deterministic backend is the source of truth for checklist status. The LLM layer is not used to decide whether an item is present, missing, incomplete, or unclear.

---

## What You Should Expect to See

The strongest demo path is:

```text
Review Package
```

In this workflow, you can upload multiple Class VI-style documents and review them as one application package.

You should expect to see:

```text
Detected document types
Missing required or expected document types
Package review metrics
Reviewer action items
Completeness checklist rows
Regulatory citations
Evidence locations and page numbers
OCR evidence labels when applicable
Reviewer confirmations
Reviewer notes
Markdown package report export
Final review packet export
Full checklist CSV export
Deficiency CSV export
Reviewer state JSON export
```

---

## Demo Safety Boundary

Please read this boundary before interpreting any output:

```text
This is a reviewer-support tool, not a final regulatory determination.
```

The system helps organize evidence and identify possible review gaps. A qualified reviewer still needs to confirm whether the cited evidence satisfies the requirement.

The system does not infer hidden redacted content.

Important boundaries:

```text
The system does not approve Class VI permits.
The system does not replace EPA or state reviewers.
The system does not guarantee regulatory compliance.
The system does not read behind redactions.
The LLM does not decide checklist status.
```

OCR-derived evidence is visible text only. If a page is redacted, the system does not inspect, recover, or infer the hidden content.

---

## Local Setup

These commands assume Windows PowerShell.

Start from the local repository:

```powershell
cd C:\Users\khali\PycharmProjects\SMART-CCUS-AI-HACKATHON
git checkout develop
git pull origin develop
```

Confirm the working tree is clean:

```powershell
git status
```

Expected output:

```text
On branch develop
Your branch is up to date with 'origin/develop'.
nothing to commit, working tree clean
```

Activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

Confirm Python is available:

```powershell
python --version
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

---

## OCR Setup

OCR support uses Tesseract.

Check that Tesseract is available:

```powershell
tesseract --version
```

Expected output should start with something like:

```text
tesseract v5...
```

If the command is not found, install Tesseract OCR, add it to your system `PATH`, close PowerShell, reopen it, reactivate `.venv`, and try again.

OCR boundary:

```text
OCR is visible text only.
The system does not inspect, recover, or infer hidden redacted content.
```

---

## Run the Test Suite

Run the full test suite before the demo:

```powershell
python -m pytest tests/
```

Expected result:

```text
passed
```

Warnings from third-party packages are acceptable if the tests pass.

Run the final demo smoke tests:

```powershell
python -m pytest tests/test_final_demo_smoke.py
python -m pytest tests/test_maip_demo_api.py
```

These smoke tests confirm that the deterministic demo endpoints and judge-facing report sections still work.

They check for:

```text
/demo/maip-package
/demo/maip-package/report
/demo/maip-package/final-packet
MAIP validation
Reviewer disclaimers
Known limitations
Completeness checklist
Deficiency table
Audit trail
```

---

## Start the FastAPI Backend

Open the first PowerShell terminal and run:

```powershell
python -m uvicorn api.main:app --reload
```

The backend should run at:

```text
http://127.0.0.1:8000
```

You can open the API docs at:

```text
http://127.0.0.1:8000/docs
```

---

## Confirm the Deterministic Demo Endpoints

With FastAPI running, open these URLs in a browser:

```text
http://127.0.0.1:8000/demo/maip-package
http://127.0.0.1:8000/demo/maip-package/report
http://127.0.0.1:8000/demo/maip-package/final-packet
```

Use these as a reliable backup demo because they do not require uploaded files, a RAG index, an LLM service, or external API calls.

### `/demo/maip-package`

This endpoint returns a deterministic JSON package-review fixture.

Show this to demonstrate:

```text
Package-level review structure
Detected documents
MAIP validation data
Source document traceability
Audit metadata
```

### `/demo/maip-package/report`

This endpoint returns the Markdown package review report.

Show this to demonstrate:

```text
Reviewer Disclaimers
Package Review Metrics
Reviewer Action Items
MAIP Cross-Reference Validation
Completeness Checklist Review
Package Coverage Evidence
Known Limitations
Audit Trail
```

### `/demo/maip-package/final-packet`

This endpoint returns the regulator-style final review packet.

Show this to demonstrate:

```text
Packet Purpose
Final Package Summary
Reviewer Disclaimers
Package Review Metrics
Reviewer Action Items
MAIP Cross-Reference Validation
Deficiency Table
Completeness Checklist Review
Known Limitations
Reviewer Sign-Off
Appendix: Full Package Review Report
Audit Trail
```

---

## Start the Streamlit UI

Open a second PowerShell terminal:

```powershell
cd C:\Users\khali\PycharmProjects\SMART-CCUS-AI-HACKATHON
.venv\Scripts\Activate.ps1
python -m streamlit run ui/app.py
```

The UI should run at:

```text
http://localhost:8501
```

In the Streamlit sidebar, use:

```text
FastAPI URL: http://127.0.0.1:8000
Chroma persist directory: chroma_data
```

---

## Primary Demo: Review Package Workflow

Use the **Review Package** tab.

Recommended demo sequence:

```text
1. Open the Review Package tab.
2. Upload multiple Class VI-style documents.
3. Click Review uploaded package.
4. Show the package summary.
5. Show detected document types.
6. Show missing required or expected document types.
7. Show package review metrics.
8. Show reviewer action items.
9. Show completeness checklist rows.
10. Show regulatory citations.
11. Show evidence locations and page numbers.
12. Show OCR source labels or redacted OCR warnings if present.
13. Add reviewer confirmations and reviewer notes.
14. Export reviewer state JSON.
15. Export full completeness checklist CSV.
16. Export deficiency CSV.
17. Export Markdown package report.
18. Export final review packet.
```

Suggested explanation:

```text
This workflow reviews a group of Class VI-style documents as one package.
The backend classifies documents, applies deterministic checklist logic, maps
findings to citations, and creates reviewer-ready outputs.
The reviewer remains responsible for confirming whether the cited evidence
actually satisfies each requirement.
```

---

## Backup Demo: Deterministic MAIP Fixture

If uploaded files, OCR, or local documents cause issues during a live demo, use the deterministic MAIP fixture.

It does not require:

```text
Uploaded files
RAG index
LLM service
External API calls
```

Use these URLs:

```text
http://127.0.0.1:8000/demo/maip-package
http://127.0.0.1:8000/demo/maip-package/report
http://127.0.0.1:8000/demo/maip-package/final-packet
```

This backup demo proves:

```text
Class VI package review structure
MAIP evidence extraction
MAIP cross-reference validation
Source document traceability
Page traceability
Audit trail metadata
Reviewer disclaimers
Known limitations
Final packet export
```

---

## OCR Validation Demo

Use this only if you want to show OCR behavior directly.

Run OCR validation on a local PDF:

```powershell
python scripts/validate_ocr_review_ingestion.py "C:\path\to\review.pdf"
```

Force OCR on all pages:

```powershell
python scripts/validate_ocr_review_ingestion.py "C:\path\to\review.pdf" --force-ocr
```

Expected output includes:

```text
Total chunks
OCR chunks
Redacted OCR chunks
Page number
Source type
Redaction detected
OCR confidence
Reviewer note
Excerpt
```

Explain this clearly:

```text
OCR is used to recover visible text from image-based pages.
OCR does not recover hidden or redacted content.
Redacted pages are flagged for reviewer caution.
```

---

## Language to Use During the Demo

Use this language when explaining the tool:

```text
This is a reviewer-support tool, not a final regulatory determination.

The deterministic backend owns checklist status, evidence detection, citations,
confidence labels, and exports.

The reviewer confirms whether the cited evidence actually satisfies the
requirement.

OCR-derived evidence is visible text only. The system does not infer hidden
redacted content.

Evidence found does not automatically mean the checklist item is complete.
```

A concise version:

```text
The system supports reviewer triage, evidence organization, and audit-ready
report generation.
```

---

## Language to Avoid

Do not describe the system this way:

```text
The system approves Class VI permits.
The system replaces EPA reviewers.
The system guarantees compliance.
The system reads behind redactions.
The LLM decides checklist status.
```

These statements are not accurate.

---

## Outputs to Show or Mention

During the demo, show or mention:

```text
Package summary
Detected document types
Missing required document types
Package review metrics
Reviewer action items
Completeness checklist review
Regulatory citations
Evidence locations
OCR source labels
Reviewer confirmations
Reviewer notes
Markdown package report
Final review packet
Full checklist CSV
Deficiency CSV
Reviewer state JSON
```

---

## Final Pre-Demo Checklist

Before presenting, confirm:

```text
[ ] develop branch is up to date
[ ] git status is clean
[ ] dependencies are installed
[ ] tesseract --version works
[ ] python -m pytest tests/ passes
[ ] final demo smoke tests pass
[ ] FastAPI starts
[ ] Streamlit starts
[ ] /demo/maip-package works
[ ] /demo/maip-package/report works
[ ] /demo/maip-package/final-packet works
[ ] Review Package tab opens
[ ] Export buttons are visible
[ ] Final packet export works
[ ] Deficiency CSV export works
[ ] Reviewer-state JSON export works
```

---

## Troubleshooting

### FastAPI is not running

Restart the backend:

```powershell
python -m uvicorn api.main:app --reload
```

Then check:

```text
http://127.0.0.1:8000/docs
```

### Streamlit cannot connect to FastAPI

Confirm the sidebar API URL is:

```text
http://127.0.0.1:8000
```

### Ask Assistant returns empty results

Use Review Package instead.

Ask Assistant requires a populated RAG index before it can provide evidence-backed answers.

### OCR does not work

Check:

```powershell
tesseract --version
```

Then try:

```powershell
python scripts/validate_ocr_review_ingestion.py "C:\path\to\review.pdf" --force-ocr
```

OCR output depends on page image quality, scan resolution, orientation, and layout.

### Tests fail because of a changed status label

Check whether the application behavior changed or whether the test is too strict.

Smoke tests should verify demo readiness without over-constraining non-critical wording.

---

## Final Architecture Summary

```text
Backend decides.
Retriever finds.
Reviewer confirms.
LLM explains.
```

Expanded:

```text
Backend decides checklist status, confidence, citations, and export structure.
Retriever finds supporting source evidence and page-located excerpts.
Reviewer confirms, revises, or rejects the finding.
LLM explains deterministic findings in reviewer-friendly language.
```