# Checklist Population Roadmap

## Purpose

The next phase of the SMART CCUS Class VI Review Assistant is to move from separate review tools into one cohesive reviewer workflow.

The target deliverable is a populated Class VI completeness checklist / reviewer workpaper. The system should allow a reviewer to upload either a single full permit application file or a multi-document project package, run a package-level review, retrieve evidence from the uploaded package, populate checklist fields, allow reviewer notes, and export the result.

This roadmap aligns the current system with teammate feedback and defines the next implementation path.

## Product Goal

The reviewer should be able to:

1. Upload one permit application file or a multi-file project package.
2. Run a package review.
3. View completeness by checklist section.
4. Open each section to inspect populated evidence.
5. See which checklist rows are present, missing, unclear, redacted, or need reviewer attention.
6. Review source file names, page numbers, excerpts, and notes.
7. Add or edit reviewer notes.
8. Use an assistant chatbot to ask follow-up questions about uploaded evidence, regulations, or guidance.
9. Export one cohesive populated review document.

## Source Checklist Structure

The Class VI completeness checklist is organized as a reviewer workpaper. It asks reviewers to mark whether information is present in the permit application and document the location of the information in the application.

Each row generally supports the following fields:

- GSDT Module/Folder
- File Name
- Page Number
- Notes

Example checklist item:

> Information required in 40 CFR 144.31(e)(1)-(6) [40 CFR 146.82(a)(1)]  
> A listing of the activities conducted by the applicant which require RCRA, UIC, NPDES, or PSD permits. [40 CFR 144.31(e)(1)]

The system should use this structure as the target output format for package review.

## Current Capabilities

The project already includes many of the required building blocks:

1. Package upload and package review.
2. Document classification.
3. Checklist-style gap analysis.
4. Evidence extraction with file and page locations.
5. Cross-document related evidence.
6. MAIP cross-reference validation.
7. Redacted evidence handling for MAIP.
8. Reviewer confirmations and notes.
9. LLM reviewer narrative.
10. Ask Assistant / RAG foundation.
11. Markdown report export.
12. Final review packet export.

## Key Architecture Principle

The system should remain reviewer-controlled and evidence-grounded.

```text
Backend decides.
Retriever finds.
Reviewer confirms.
LLM explains.

```

## What the LLM Does

The LLM is not the source of truth.

The LLM may:

- Summarize deterministic backend findings.
- Explain retrieved evidence in clearer reviewer-facing language.
- Help draft notes based on cited evidence.
- Help the reviewer understand relevant guidance or regulatory context.
- Assist with natural-language follow-up questions.

The LLM must not:

- Invent missing values.
- Invent page numbers.
- Invent file names.
- Change checklist statuses.
- Change severity.
- Change reviewer disposition.
- Override deterministic backend findings.
- Treat uncited text as verified evidence.
- Infer redacted values.

For checklist population, the retrieval system finds candidate evidence, the backend controls structured fields and statuses, the reviewer confirms or edits, and the LLM explains.

## Target Workflow

### 1. Package Upload

The reviewer uploads either:

- A single full permit application file, or
- A multi-document package.

The system performs temporary ingestion and review.

### 2. Temporary Package Retrieval Layer

Uploaded package content is split into chunks with metadata:

- Source file
- Page number
- Section heading, if available
- Extracted text
- Table context, if available
- Document type
- Plan type
- Local package identifier

These chunks should be searchable during the review session.

### 3. Checklist Row Retrieval

Each checklist row becomes a structured retrieval task.

For each checklist row, the system should use:

- Checklist item text
- CFR citation
- Section title
- Related keywords
- Expected plan type
- Existing package review findings
- Retrieved evidence from uploaded package chunks

### 4. Field Population

For each row, the system should populate:

- Status
- GSDT Module/Folder
- File Name
- Page Number
- Evidence excerpt
- System notes
- Reviewer notes
- Reviewer confirmation state

### 5. Reviewer Section Dashboard

The reviewer should see major checklist sections with status indicators.

Example:

```text
GENERAL INFORMATION                         Green / Yellow / Red
GEOLOGIC NARRATIVE / SITE CHARACTERIZATION  Green / Yellow / Red
PLANNED WELL OPERATIONS                     Green / Yellow / Red
AREA OF REVIEW AND CORRECTIVE ACTION        Green / Yellow / Red
TESTING AND MONITORING PLAN                 Green / Yellow / Red
INJECTION WELL PLUGGING PLAN                Green / Yellow / Red
PISC AND SITE CLOSURE PLAN                  Green / Yellow / Red
EMERGENCY AND REMEDIAL RESPONSE PLAN        Green / Yellow / Red
INJECTION WELL CONSTRUCTION PLAN            Green / Yellow / Red
PRE-OPERATIONAL TESTING                     Green / Yellow / Red
FINANCIAL RESPONSIBILITY DEMONSTRATION      Green / Yellow / Red
PROPOSED STIMULATION PLAN                   Optional / Present / Missing
INJECTION DEPTH WAIVER REQUEST              Optional / Present / Missing
MAIP CROSS-REFERENCE VALIDATION             Pass / Warning / Missing / Redacted
```

### 6. Export

The final export should include:

1. Package summary.
2. Section-level completeness summary.
3. Populated checklist rows.
4. File and page evidence locations.
5. MAIP validation.
6. Redacted evidence notes.
7. Reviewer confirmations.
8. Reviewer notes.
9. Remaining action items.

## Checklist Row Output Model

Each populated checklist row should eventually support a structure like:

```json
{
  "section_title": "GENERAL INFORMATION",
  "checklist_item": "A listing of the activities conducted by the applicant which require RCRA, UIC, NPDES, or PSD permits.",
  "citation": "40 CFR 144.31(e)(1)",
  "status": "present",
  "gsdt_module_folder": "",
  "file_name": "Project_Narrative.pdf",
  "page_number": 12,
  "evidence_excerpt": "The applicant lists permits required under UIC, NPDES, and PSD programs...",
  "system_notes": "Candidate evidence found in project narrative.",
  "reviewer_notes": "",
  "reviewer_confirmation": "pending_review",
  "confidence": "medium"
}
```

## Status Definitions

Suggested row statuses:

- `present`: Evidence found with adequate source location.
- `missing`: No relevant evidence found.
- `unclear`: Some related evidence found, but it does not clearly satisfy the row.
- `redacted`: Relevant evidence appears present but is redacted or unreadable.
- `needs_reviewer_attention`: Evidence found, but reviewer judgment is needed.
- `not_applicable_optional`: Optional item does not appear applicable.

Suggested section indicators:

- Green: Most required rows present and no critical missing rows.
- Yellow: Some rows unclear, low-confidence, redacted, or need reviewer attention.
- Red: Required rows missing or critical evidence unavailable.
- Gray: Optional or not applicable section.

## Relationship to Ask Assistant

The Ask Assistant remains useful, but it should not be the main output.

Current Ask Assistant:

- User asks a question.
- System retrieves evidence.
- Assistant provides an answer.

Checklist Population Engine:

- Checklist row asks the question automatically.
- System retrieves evidence for that row.
- Backend maps retrieved evidence into checklist fields.
- Reviewer confirms or edits.
- Exported checklist becomes the final product.

## Relationship to Package Review

The current package review identifies:

- Detected document types
- Missing document types
- Duplicate document types
- Unknown documents
- Checklist row coverage
- Evidence locations
- Page references
- Missing and unclear rows
- Reviewer action items

The checklist population engine should reuse these outputs rather than duplicate them.

## Relationship to MAIP Validation

MAIP cross-reference validation should remain a specialized deterministic sub-check.

For pressure values:

- Numeric values must be extracted before comparison.
- Redacted values must not be inferred.
- Redacted evidence should require reviewer verification from confidential/unredacted materials.
- LLM narrative may explain the result but must not change it.

## Implementation Phases

### Phase 1: Roadmap and Alignment

Add this roadmap document to the repository.

### Phase 2: Checklist Row Data Model

Create a structured model for populated checklist rows and section summaries.

Potential files:

- `review/checklist_population.py`
- `tests/test_checklist_population.py`

### Phase 3: Checklist Row Query Builder

Create deterministic retrieval queries from checklist rows.

Inputs:

- Checklist item
- Citation
- Section title
- Related terms
- Expected plan type

Output:

- Query string
- Required terms
- Optional terms
- Expected evidence type

### Phase 4: Package Evidence Matching

Connect populated checklist rows to package review findings and temporary retrieved chunks.

The first version can use existing package review evidence before introducing a deeper temporary vector-store loop.

### Phase 5: Export Populated Checklist

Add markdown export for populated checklist rows.

Potential output:

- Section summary
- Row status
- File name
- Page number
- Evidence excerpt
- Reviewer notes

### Phase 6: UI Section Dashboard

Add section-level expanders with status indicators and editable reviewer notes.

### Phase 7: Assistant Sidebar

Use Ask Assistant as a support tool for follow-up questions about:

- The uploaded package
- EPA guidance
- 40 CFR requirements
- Why a row is missing, unclear, or redacted

## Demo Explanation

The system turns a Class VI completeness checklist into a guided review workflow.

Instead of manually searching hundreds or thousands of pages, the reviewer uploads the package and the assistant populates checklist fields with evidence locations, excerpts, and notes. The reviewer remains in control and confirms or edits the output.

The LLM helps explain findings, but the backend and retrieved evidence control statuses, citations, page numbers, and reviewer-facing action items.

## Open Questions

1. Should the populated checklist export be Markdown first, then DOCX/XLSX later?
2. Should the temporary package retrieval index be stored only in memory/session storage?
3. Should GSDT Module/Folder be inferred from document type, manually entered, or left blank when unavailable?
4. Should section-level green/yellow/red thresholds be configurable?
5. Should reviewer edits be persisted to JSON for later reload?
6. Should the package-scoped Ask Assistant search only uploaded package evidence by default, or both package evidence and EPA guidance?