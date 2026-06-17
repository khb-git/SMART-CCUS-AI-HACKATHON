# SMART CCUS Demo Readiness Checklist

This checklist is the recommended runbook for demonstrating the SMART CCUS Class VI Review Assistant.

Core architecture:

```text
Backend decides.
Reviewer confirms.
LLM explains.
```

The deterministic backend is the source of truth for checklist status, MAIP validation, evidence locations, citations, severity, reviewer action items, and export structure. Reviewer confirmations annotate the findings. The LLM layer provides narrative explanation only.

---

## 1. Pre-Demo Setup

### Confirm branch and environment

```powershell
git checkout develop
git pull origin develop
python -m pytest tests/
```

Expected result:

```text
All tests pass.
```

### Start FastAPI

Terminal 1:

```powershell
python -m uvicorn api.main:app --reload
```

Confirm FastAPI is available:

```text
http://127.0.0.1:8000/docs
```

Optional direct endpoint checks:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/demo/maip-package
http://127.0.0.1:8000/demo/maip-package/report
http://127.0.0.1:8000/demo/maip-package/final-packet
```

### Start Streamlit

Terminal 2:

```powershell
python -m streamlit run ui/app.py
```

Open:

```text
http://localhost:8501
```

Sidebar settings:

```text
FastAPI URL: http://127.0.0.1:8000
Chroma persist directory: chroma_data
```

---

## 2. Recommended Demo Path

Use this flow for the strongest and most reliable demo.

```text
Review Package tab
→ Load deterministic MAIP demo package
→ inspect deterministic package review
→ inspect MAIP validation
→ add reviewer confirmations or notes
→ generate reviewer narrative
→ download final review outputs
```

This path does not require uploaded files, RAG indexing, or a local LLM.

---

## 3. Streamlit Demo Walkthrough

### Step 1 — Open Review Package

Go to:

```text
Review Package
```

Point out:

```text
This is the main reviewer workflow.
Uploaded documents are processed temporarily.
The deterministic backend performs the package review.
```

### Step 2 — Load the deterministic MAIP demo package

Click:

```text
Load deterministic MAIP demo package
```

Expected result:

```text
Displaying deterministic MAIP demo package.
Package: maip_demo_package
```

Explain:

```text
This loads an in-memory Class VI package designed to exercise the MAIP workflow.
It does not use uploaded files, RAG, or an LLM.
```

### Step 3 — Show package-level results

Show:

```text
Overall status
Detected document types
Missing required document types
Package Review Metrics
Reviewer Action Items
```

Explain:

```text
The package can still have a Needs Review package status even when MAIP passes.
The package status reflects overall application completeness.
The MAIP status reflects only the MAIP cross-reference checks.
```

### Step 4 — Show MAIP Cross-Reference Validation

Scroll to:

```text
MAIP Cross-Reference Validation
```

Expected demo values:

```text
MAIP status: Pass
MAIP findings: 7
Missing evidence: 0
```

Expected supporting values:

```text
proposed_maip: 1800.0 psi
fracture_pressure: 2200.0 psi
aor_model_max_pressure: 2000.0 psi
casing_pressure_rating: 3000.0 psi
annulus_management_evidence
operating_margin_evidence
```

Explain:

```text
MAIP validation is deterministic.
The backend extracts conservative pressure evidence from checklist findings.
The validator checks the proposed MAIP against fracture pressure, AoR model pressure, casing rating, annulus evidence, and operating-margin evidence.
```

### Step 5 — Show audit trail

In the MAIP table, point out:

```text
source file
page number
matched term
source finding ID
extraction method
confidence
```

Explain:

```text
The audit trail is what makes the MAIP result reviewable.
The system does not simply say pass/fail. It shows why the result was produced.
```

### Step 6 — Show reviewer confirmations

Open:

```text
Reviewer confirmations for MAIP findings
Reviewer confirmations
```

Use one example:

```text
Reviewer Confirmation: Confirmed
Reviewer Notes: Cited MAIP evidence confirmed for demo.
```

Explain:

```text
Reviewer confirmations do not rewrite the backend result.
They capture human disposition and notes for export.
```

### Step 7 — Generate reviewer narrative

Scroll to:

```text
Reviewer Narrative
```

Leave unchecked unless Ollama is installed:

```text
Use local LLM if available
```

Click:

```text
Generate reviewer narrative
```

Expected result:

```text
Backend decides. Reviewer confirms. LLM explains.
```

Explain:

```text
The narrative is generated from deterministic findings.
It does not change checklist status, MAIP status, evidence, citations, page numbers, severity, or reviewer confirmations.
If a local LLM is unavailable, the system falls back to a deterministic template.
```

### Step 8 — Download reviewer outputs

Download:

```text
Reviewer narrative Markdown
Markdown package review report with reviewer confirmations
Final review packet
Completeness checklist CSV
Deficiency CSV
MAIP deficiency CSV
Reviewer state JSON
```

Explain:

```text
These exports are reviewer-ready artifacts.
They preserve deterministic findings, citations, page evidence, MAIP audit trail, and reviewer notes.
```

---

## 4. Optional Uploaded-Package Demo

Use uploaded documents only after the deterministic demo is working.

Flow:

```text
Review Package tab
→ upload PDF/DOCX/XLSX application documents
→ click Review uploaded package
→ inspect package review
→ inspect MAIP validation
→ generate reviewer narrative
→ download exports
```

Important expected behavior:

```text
Actual uploaded documents may show MAIP Missing Evidence.
That is not a failure.
It means deterministic extraction did not find enough structured MAIP evidence.
```

Explain:

```text
The system is conservative. It reports missing evidence rather than inferring pressure values from weak text.
```

---

## 5. Ask Assistant Boundary

The Ask Assistant tab is separate from deterministic package review.

Use only when a RAG index has been built:

```text
data/raw_docs/
data/chunked/
chroma_data/
```

If no RAG index is available, use:

```text
Review Package
```

for the main demo.

Explain:

```text
Ask Assistant is retrieval-augmented Q&A.
Review Package is deterministic checklist and package review.
They are separate workflows.
```

---

## 6. Local LLM Notes

The UI includes:

```text
Use local LLM if available
```

This requires Ollama to be installed separately.

If Ollama is not installed, leave the checkbox unchecked. The deterministic template narrative still works.

Optional local LLM commands after installing Ollama:

```powershell
ollama pull llama3.1
ollama serve
```

Then rerun the narrative with:

```text
Use local LLM if available = checked
```

The system still preserves the same boundary:

```text
Backend decides.
Reviewer confirms.
LLM explains.
```

---

## 7. Demo Talking Points

### Main one-liner

```text
This is a reviewer-support system for Class VI carbon storage applications. It uses deterministic logic to produce auditable package findings, then allows the reviewer to confirm or annotate those findings, and finally uses an LLM only to explain the deterministic result.
```

### Architecture explanation

```text
Backend decides: checklist status, MAIP status, evidence, citations, severity, and exports.
Reviewer confirms: human reviewer disposition and notes.
LLM explains: narrative summary over backend findings.
```

### MAIP explanation

```text
MAIP validation is integrated into real package review. The deterministic demo is just a reliable sample package for showing the full workflow without uploaded files.
```

### Safety explanation

```text
The LLM is not allowed to override the deterministic backend. If the backend says evidence is missing, the LLM must explain that evidence is missing rather than inventing a value.
```

### Auditability explanation

```text
The system shows source document, page number, matched term, extraction method, confidence, and recommended reviewer action.
```

---

## 8. Quick Failure Recovery

### FastAPI is not reachable

Check Terminal 1:

```powershell
python -m uvicorn api.main:app --reload
```

Check browser:

```text
http://127.0.0.1:8000/docs
```

### Streamlit cannot reach backend

Check sidebar:

```text
FastAPI URL: http://127.0.0.1:8000
```

### Demo button loads but results do not appear

Refresh Streamlit and click:

```text
Load deterministic MAIP demo package
```

Expected:

```text
Displaying deterministic MAIP demo package.
Package: maip_demo_package
```

### Reviewer narrative fails

Leave unchecked:

```text
Use local LLM if available
```

Then click:

```text
Generate reviewer narrative
```

The deterministic template fallback should work without Ollama.

### Uploaded package shows MAIP Missing Evidence

Expected for incomplete or unclear uploaded files.

Explain:

```text
The backend did not find enough structured MAIP evidence. It reports missing evidence rather than guessing.
```

---

## 9. Final Pre-Demo Checklist

Before presenting, confirm:

```text
[ ] FastAPI starts without errors
[ ] Streamlit starts without errors
[ ] /health returns ok
[ ] /demo/maip-package returns maip_demo_package
[ ] Review Package tab loads deterministic MAIP demo
[ ] MAIP status displays Pass
[ ] Audit Trail column is visible
[ ] Reviewer confirmations can be selected
[ ] Reviewer narrative generates with local LLM unchecked
[ ] Reviewer narrative Markdown downloads
[ ] Final review packet downloads
[ ] MAIP deficiency CSV downloads
[ ] Full test suite passes
```

Final validation command:

```powershell
python -m pytest tests/
```