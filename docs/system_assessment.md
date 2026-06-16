# SMART CCUS AI System Assessment

## Current System State

The SMART CCUS Class VI Review Assistant has reached a strong deterministic review foundation. The system now supports document-level and package-level review workflows, with reviewer-facing outputs that are grounded in checklist logic, evidence locations, confidence labels, regulatory citations, and human review controls.

The current design principle remains:

```text
Backend decides.
Reviewer confirms.
LLM explains.
```

The backend should continue to own deterministic review status, evidence extraction, checklist mapping, citation mapping, metrics, and export structure. The LLM layer should only explain, summarize, and help reviewers interpret already-computed outputs.

---

## Production-Ready Foundations

The following pieces are strong enough to treat as core system infrastructure.

### 1. Document Review

The system can review individual uploaded PDF, DOCX, and XLSX files against Class VI checklist logic.

Current strengths:

- Temporary document ingestion
- Plan/document classification
- Checklist finding generation
- Status labels: `present`, `evidence_found`, `missing`, `unclear`
- Severity and requirement-level handling
- Supporting excerpts
- Evidence locations where available
- Markdown review report export

---

### 2. Package Review

The system can review multiple uploaded documents as one Class VI package.

Current strengths:

- Package-level document classification
- Expected vs detected plan type checks
- Missing required document type detection
- Duplicate document type detection
- Unknown/supporting document handling
- Per-document review summaries
- Package coverage evidence
- Package-level Markdown report export

---

### 3. Completeness Checklist View

The system now reformats package findings into an EPA-style completeness checklist structure.

Current checklist columns:

- Status
- Required Item
- GSDT Module/Folder
- Regulatory Citation
- File Name
- Page Number
- Notes

This is one of the most important reviewer-facing outputs because it mirrors how a regulator or technical reviewer thinks through an application package.

---

### 4. Evidence Location Support

Checklist rows include location-oriented evidence when available.

Current location fields include:

- File name
- Page number
- Chunk index
- Section heading
- Excerpt
- Matched terms

This makes findings more auditable and reduces the risk of unsupported review conclusions.

---

### 5. Cross-Document Related Evidence

The system can identify related evidence elsewhere in the package without automatically changing the finding status.

This is important because related evidence may help the reviewer resolve ambiguity, but it should not automatically convert a missing item into a compliant item.

The current behavior is correct:

```text
Related package evidence supports reviewer investigation.
It does not override deterministic checklist status.
```

---

### 6. Deterministic Confidence Labels

Findings include deterministic confidence levels.

Current labels:

- High
- Medium
- Low
- Unknown

These confidence labels are useful for reviewer prioritization and should remain backend-computed.

---

### 7. Package Metrics

The system computes package-level review metrics, including:

- Total checklist rows
- Present rows
- Evidence-found rows
- Missing rows
- Unclear rows
- Required missing rows
- Critical missing rows
- High-confidence rows
- Medium-confidence rows
- Low-confidence rows
- Page-located rows
- Page-located evidence percent
- Resolved percent

These metrics give reviewers a quick health check before reading row-level findings.

---

### 8. Reviewer Action Items

The backend generates deterministic reviewer action items from package findings and metrics.

Examples include:

- Resolve critical missing checklist rows
- Resolve required missing checklist rows
- Review evidence-found rows
- Review low-confidence rows
- Add or verify page references
- Confirm cross-document related evidence

These are backend-generated, deterministic next steps.

---

### 9. Reviewer Confirmation Workflow

The Streamlit UI now supports session-only human review controls.

Reviewer confirmation options:

- Pending review
- Confirmed
- Needs follow-up
- Not applicable
- Resolved after cross-reference

This gives the reviewer a human-in-the-loop layer without changing backend finding status.

---

### 10. Reviewer Notes

The Streamlit UI supports session-only reviewer notes for each checklist row.

These notes allow reviewers to capture comments such as:

- Need updated cost table.
- Confirm with appendix.
- Cross-reference page 7 of project narrative.
- Applicant should clarify monitoring frequency.

Reviewer notes are included in exports.

---

### 11. Reviewer Filters and Summary

The package review UI supports:

- Checklist status filtering
- Reviewer confirmation filtering
- Reviewer confirmation summary metrics

This makes large package reviews more manageable.

---

### 12. Exports

The system currently supports:

- Markdown document review report
- Markdown package review report
- Markdown reviewer confirmation export
- CSV completeness checklist export

The CSV export is especially useful for Excel-based review workflows.

---

### 13. Regulatory Citation Mapping

Checklist rows now include deterministic Class VI regulatory citation mapping at the plan/module level.

Examples:

- Financial Responsibility → `40 CFR 146.85 - Financial responsibility`
- Testing and Monitoring → `40 CFR 146.90 - Testing and monitoring requirements`; `40 CFR 146.91 - Reporting requirements`
- PISC and Site Closure → `40 CFR 146.93 - Post-injection site care and site closure`

This strengthens the backend truth layer before adding an LLM explanation layer.

---

## Current Limitations

### 1. Reviewer Confirmations Are Session-Only

Reviewer confirmations and reviewer notes are currently stored only in Streamlit session state.

This means they are preserved only if the reviewer exports the Markdown or CSV report.

Recommended future branch:

```text
feature/add-reviewer-confirmation-persistence
```

---

### 2. Regulatory Citations Are Plan-Level, Not Item-Level

Current citation mapping is deterministic but broad.

For example, every financial responsibility checklist row maps to:

```text
40 CFR 146.85 - Financial responsibility
```

Future improvement should add item-level citation mapping where possible.

Recommended future branch:

```text
feature/add-item-level-regulatory-citations
```

---

### 3. LLM Explanation Layer Has Not Been Added Yet

This is intentional.

The deterministic backend should remain the source of truth. The LLM should be added only after the backend outputs are stable enough to explain.

Recommended future branch:

```text
feature/add-llm-review-narrative-layer
```

---

### 4. Exports Could Be More Regulator-Ready

Current Markdown and CSV exports are useful, but the final review packet could be improved with:

- Executive summary
- Deficiency table
- Reviewer sign-off section
- Appendix-style evidence table
- Citation summary
- Applicant follow-up request list

Recommended future branch:

```text
feature/add-final-review-packet-export
```

---

### 5. UI Could Eventually Be Split Further

The `ui/app.py` file is cleaner after moving reviewer workflow helpers, but it still contains multiple major UI workflows:

- Ask Assistant
- Review Document
- Review Package

Future cleanup could split rendering into smaller modules.

Recommended future branch:

```text
chore/split-streamlit-tab-renderers
```

---

## Recommended Next Branches

### 1. `feature/add-item-level-regulatory-citations`

Move from plan-level citations to checklist-item-level citations where possible.

Why this should come next:

- Strengthens deterministic backend
- Improves reviewer trust
- Makes future LLM explanations more precise

---

### 2. `feature/add-final-review-packet-export`

Create a regulator-style review packet that combines:

- Package summary
- Package metrics
- Reviewer action items
- Deficiency table
- Completeness checklist
- Reviewer confirmations
- Reviewer notes
- Regulatory citations
- Evidence locations

---

### 3. `feature/add-reviewer-confirmation-persistence`

Persist reviewer confirmations and notes beyond the current Streamlit session.

Potential storage options:

- Local JSON file
- SQLite
- Backend endpoint
- Project/package-specific review state file

---

### 4. `feature/add-llm-review-narrative-layer`

Add the LLM only after deterministic outputs are stable.

The LLM should:

- Explain findings
- Summarize deficiencies
- Draft reviewer narratives
- Draft applicant follow-up language
- Never invent evidence
- Never override backend status

---

### 5. `chore/split-streamlit-tab-renderers`

Split Streamlit rendering into smaller files to improve maintainability.

Potential files:

```text
ui/ask_tab.py
ui/review_document_tab.py
ui/review_package_tab.py
ui/reviewer_workflow.py
```

---

## Recommended Immediate Direction

The next best feature branch is:

```text
feature/add-item-level-regulatory-citations
```

Reason:

The system already has plan-level citation anchors. Item-level citation mapping would make the checklist rows more precise and make future LLM explanations safer.

The LLM should come after this, not before it.

---

## Current Readiness Summary

| Area | Status |
| --- | --- |
| Document review | Strong foundation |
| Package review | Strong foundation |
| Completeness checklist view | Strong foundation |
| Evidence locations | Strong foundation |
| Cross-document related evidence | Strong foundation |
| Confidence levels | Strong foundation |
| Package metrics | Strong foundation |
| Reviewer action items | Strong foundation |
| Reviewer confirmations | Functional, session-only |
| Reviewer notes | Functional, session-only |
| Markdown export | Functional |
| CSV export | Functional |
| Regulatory citations | Functional, plan-level |
| Item-level citations | Not yet implemented |
| Reviewer persistence | Not yet implemented |
| LLM explanation layer | Not yet implemented |
| Final regulator-style packet | Not yet implemented |

---

## Guiding Principle Going Forward

Before adding generative AI, the deterministic system should answer:

```text
What is missing?
Where is the evidence?
What regulation does it relate to?
How confident is the system?
What should the reviewer check next?
What did the reviewer confirm?
What notes did the reviewer add?
```

Once those answers are stable, the LLM can safely explain them.