# MAIP Cross-Reference Validation Plan and Workflow Status

## Purpose

This document summarizes the implemented Maximum Allowable Injection Pressure validation workflow for the SMART CCUS Class VI Review Assistant.

The MAIP workflow adds deterministic cross-reference checking on top of the package review engine. It connects pressure evidence across Class VI application materials and emits reviewer-facing findings for missing evidence, warnings, and failures.

The workflow follows the project architecture:

```text
Backend decides.
Reviewer confirms.
LLM explains.
```

The backend extracts conservative structured evidence, applies deterministic validation rules, and emits findings. Reviewers confirm or annotate the findings. A future LLM layer may explain the results, but it should not decide MAIP validity.

The validator should be deterministic: it should extract or receive structured values, apply explicit rules, and emit reviewer-facing findings without using an LLM to decide validity.
---

## Why MAIP Validation Matters

For Class VI review, injection pressure must remain below conditions that could fracture the confining system or compromise containment.

The MAIP workflow checks the chain:

```text
fracture pressure
→ MAIP at 90% fracture pressure
→ AoR model pressure constraint
→ casing adequacy
→ annulus management
→ operating margin
```

A break in this chain should become a reviewer-facing finding because it may indicate inconsistency between the operating plan, geologic basis, AoR modeling, well design, monitoring plan, and containment assumptions.

---

## Implemented Status

The MAIP workflow is now implemented across the deterministic package review path.

Current implemented capabilities:

```text
deterministic MAIP validation dataclasses
deterministic MAIP validation rules
package-review integration
Markdown package report integration
final review packet integration
Streamlit MAIP validation panel
conservative MAIP evidence extraction
reviewer confirmation and reviewer notes for MAIP findings
dedicated MAIP reviewer export section
dedicated MAIP deficiency CSV export
MAIP evidence audit trail
MAIP audit trail export in Markdown reports
deterministic MAIP demo sample package
```

---

## Implemented Files

Core implementation:

```text
review/maip_validation.py
review/package_review.py
review/report_export.py
ui/app.py
ui/reviewer_workflow.py
```

Demo fixture:

```text
demo_samples/maip_demo_package.py
```

Representative tests:

```text
tests/test_maip_validation.py
tests/test_package_maip_validation_integration.py
tests/test_maip_evidence_extraction.py
tests/test_maip_export_support.py
tests/test_streamlit_completeness_checklist_view.py
tests/test_maip_demo_sample.py
```

---

## Data Model

The implemented validator uses structured deterministic objects.

### `MaipEvidenceValue`

Represents one extracted or structured evidence value.

Key fields:

```text
concept
value
unit
source_file
page_number
excerpt
confidence
source_finding_id
source_label
matched_term
extraction_method
extraction_notes
```

The audit fields make extracted values traceable to the checklist finding and concept term that produced them.

### `MaipValidationInput`

Carries optional structured inputs for the validation chain.

Implemented fields:

```text
proposed_maip
fracture_pressure
fracture_gradient
aor_model_max_pressure
casing_pressure_rating
annulus_pressure_limit
operating_pressure_limit
annulus_management_evidence
operating_margin_evidence
```

All fields remain optional because real application packages may be incomplete.

### `MaipValidationFinding`

Represents one deterministic validation finding.

Key fields:

```text
finding_id
status
severity
message
recommended_action
supporting_values
```

### `MaipValidationReport`

Represents the full MAIP validation result.

Key fields:

```text
overall_status
summary
findings
```

---

## Implemented Validation Rules

### Rule 1: Proposed MAIP evidence must be present

If proposed MAIP is missing:

```text
status: missing_evidence
severity: high
```

Reviewer message:

```text
The package does not provide a clear proposed Maximum Allowable Injection Pressure.
```

### Rule 2: Fracture pressure or fracture gradient evidence must be present

If neither fracture pressure nor fracture gradient evidence is available:

```text
status: missing_evidence
severity: high
```

Reviewer message:

```text
The package does not provide clear fracture pressure or fracture gradient evidence needed to verify the proposed MAIP.
```

### Rule 3: Proposed MAIP should not exceed 90% of fracture pressure

When both proposed MAIP and fracture pressure are available:

```text
proposed_maip <= 0.90 * fracture_pressure
```

If proposed MAIP exceeds the threshold:

```text
status: fail
severity: critical
```

If proposed MAIP is close to the threshold:

```text
0.85 * fracture_pressure < proposed_maip <= 0.90 * fracture_pressure
status: warning
severity: moderate
```

### Rule 4: Proposed MAIP should not exceed AoR model pressure assumptions

When both proposed MAIP and AoR model maximum pressure are available:

```text
proposed_maip <= aor_model_max_pressure
```

If proposed MAIP exceeds the AoR model pressure constraint:

```text
status: fail
severity: high
```

### Rule 5: Proposed MAIP should be below casing pressure rating

When both proposed MAIP and casing pressure rating are available:

```text
proposed_maip < casing_pressure_rating
```

If proposed MAIP is not below the casing pressure rating:

```text
status: fail
severity: critical
```

### Rule 6: Annulus pressure management evidence should be present

If annulus pressure or annulus management evidence is absent:

```text
status: warning
severity: moderate
```

### Rule 7: Operating margin evidence should be present

If operating margin evidence is absent:

```text
status: warning
severity: moderate
```

---

## Conservative Evidence Extraction

MAIP extraction is intentionally conservative.

The extractor only creates structured values when a known MAIP-related concept term and a clear pressure value appear in the same checklist finding text or evidence excerpt.

Supported pressure units include:

```text
psi
psig
pounds per square inch
```

Supported numeric concepts include:

```text
proposed_maip
fracture_pressure
fracture_gradient
aor_model_max_pressure
casing_pressure_rating
annulus_pressure_limit
operating_pressure_limit
```

Supported non-numeric evidence concepts include:

```text
annulus_management_evidence
operating_margin_evidence
```

The extractor includes a negation guard so statements such as “does not identify MAIP” are not treated as valid MAIP evidence.

---

## Audit Trail

Extracted MAIP values include audit metadata:

```text
source_finding_id
source_label
matched_term
extraction_method
extraction_notes
source_file
page_number
excerpt
confidence
```

This allows reviewers to see why a value was extracted and where it came from.

Audit information is visible in:

```text
Streamlit MAIP validation panel
Markdown package report
final review packet
MAIP demo sample output
```

---

## Reviewer Workflow

MAIP findings are reviewer-confirmable in the Streamlit Review Package workflow.

Supported reviewer confirmation values:

```text
Pending review
Confirmed
Needs follow-up
Not applicable
Resolved after cross-reference
```

Reviewers can also add notes for each MAIP finding.

MAIP reviewer rows are included in:

```text
general reviewer confirmation export
dedicated MAIP reviewer confirmation export
reviewer state JSON export
```

---

## Exports

The MAIP workflow is included in the package export path.

Implemented outputs:

```text
Markdown package review report
final review packet
dedicated MAIP reviewer confirmation section
dedicated MAIP deficiency CSV
MAIP audit trail in Markdown tables
reviewer state JSON
```

The standard checklist deficiency CSV remains checklist-specific. MAIP deficiency export is intentionally separate so reviewers can distinguish checklist completeness issues from MAIP cross-reference issues.

---

## Demo Fixture

A deterministic MAIP demo package is available:

```powershell
python -m demo_samples.maip_demo_package
```

The demo fixture does not require uploaded files, RAG, or an LLM.

It exercises:

```text
conservative MAIP evidence extraction
MAIP validation
audit trail metadata
Markdown package report export
final review packet export
```

Run demo tests:

```powershell
python -m pytest tests/test_maip_demo_sample.py
```

---

## Non-Goals

The MAIP workflow does not:

```text
use an LLM to decide MAIP validity
replace checklist review
require the RAG index
require Ask Assistant
perform broad unvalidated numeric extraction
change package review status decisions without deterministic findings
```

---

## Relationship to LLM Layer

A future LLM narrative layer can explain MAIP validation findings, but it should receive deterministic MAIP results as input.

Recommended LLM input:

```text
MAIP finding
+ deterministic status
+ severity
+ proposed MAIP
+ fracture pressure
+ 90% threshold
+ AoR model pressure evidence
+ casing pressure evidence
+ annulus evidence
+ operating margin evidence
+ source excerpts
+ audit trail metadata
+ reviewer confirmation
+ reviewer notes
→ LLM-generated reviewer explanation
```

The LLM should improve readability, not replace the validator.

---

## Implemented Branch History

The MAIP workflow was implemented through staged feature branches:

```text
feature/add-maip-validation-core
feature/add-maip-package-review-integration
feature/add-maip-export-support
feature/add-maip-ui-panel
feature/add-maip-evidence-extraction
feature/add-maip-reviewer-confirmation-support
feature/add-maip-reviewer-export
feature/add-maip-deficiency-export
feature/add-maip-evidence-audit-trail
feature/add-maip-audit-export
feature/add-maip-demo-sample
fix/maip-demo-sample-status
```

These branches moved the MAIP feature from a planned deterministic validator into an implemented package-review subsystem.


---

## Current Decision

The MAIP workflow is now a completed deterministic review subsystem within the package review path.

Remaining future work should focus on:

```text
improving table-aware pressure extraction
adding more real-document regression tests
adding FastAPI integration tests with MAIP fixture packages
improving reviewer-facing wording
eventually adding LLM narrative explanation over deterministic MAIP results
```