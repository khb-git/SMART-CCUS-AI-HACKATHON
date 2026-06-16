MAIP Cross-Reference Validation Plan
Purpose
This document defines the planned deterministic Maximum Allowable Injection Pressure validation layer for the SMART CCUS Class VI Review Assistant.
The current system performs strong checklist-based completeness review across Class VI plan types. The MAIP validation layer will add cross-section consistency checking on top of that review engine.
This work reconnects the current 11-plan-type implementation to the original methodology-centered plan, where MAIP validation was the conceptual centerpiece.
---
Guiding Principle
The MAIP validator should follow the project architecture:
```text
Backend decides.
Reviewer confirms.
LLM explains.
```
The validator should be deterministic. It should extract or receive structured values, apply explicit rules, and emit reviewer-facing findings. An LLM may later explain the result, but it should not decide whether the MAIP chain is valid.
---
Why MAIP Validation Matters
For Class VI review, injection pressure must remain below pressure conditions that could fracture the confining system or compromise containment.
The original project plan centered on a cross-reference chain linking:
```text
fracture pressure
→ MAIP at 90% fracture pressure
→ AoR model pressure constraint
→ casing adequacy
→ annulus management
→ operating margin
```
A break in this chain should become a high-severity reviewer finding because it may indicate that the operating plan, well design, monitoring plan, and containment assumptions are not internally consistent.
---
Current State
The current `develop` branch has:
```text
11 Class VI plan-type YAML checklists
105 checklist review items
deterministic gap analysis
evidence locations
regulatory citations
cross-document related evidence
reviewer confirmations
final review packet export
deficiency CSV export
```
The current branch does not yet have a deterministic MAIP cross-reference validator.
The existing cross-document related evidence feature is useful, but it is not the same as checking whether fracture pressure, proposed MAIP, AoR pressure assumptions, casing capacity, annulus behavior, and operating margin are numerically and conceptually consistent.
---
Planned Validator Scope
The first MAIP validator should check whether the package contains enough evidence to support the chain and whether the extracted values satisfy basic deterministic consistency rules.
The initial scope should cover:
```text
fracture pressure evidence
proposed MAIP evidence
90% fracture-pressure limit
AoR model pressure constraint evidence
casing pressure adequacy evidence
annulus pressure / annulus management evidence
operating margin evidence
```
---
Relevant Plan Types
The validator should operate across the 11-plan-type structure already implemented.
Likely source plan types:
```text
site_geologic_characterization
aor_corrective_action
well_construction
site_operating
testing_monitoring
emergency_remedial_response
project_narrative
```
Possible relationships:
Concept	Likely source plan type
Fracture pressure / fracture gradient	`site_geologic_characterization`
AoR pressure constraint / plume-pressure model	`aor_corrective_action`
Casing pressure rating / well integrity	`well_construction`
Proposed MAIP / injection pressure limit	`site_operating`
Annulus pressure monitoring	`testing_monitoring`
Operating margin and response triggers	`site_operating`, `testing_monitoring`, `emergency_remedial_response`
---
Planned Data Model
The validator should use a small structured model rather than parsing everything inside one function.
Potential dataclasses:
```text
MaipEvidenceValue
MaipValidationInput
MaipValidationFinding
MaipValidationReport
```
`MaipEvidenceValue`
Recommended fields:
```text
concept
value
unit
source_file
page_number
excerpt
confidence
```
Examples of concepts:
```text
fracture_pressure
fracture_gradient
proposed_maip
aor_model_max_pressure
casing_pressure_rating
annulus_pressure_limit
operating_pressure_limit
```
`MaipValidationInput`
Recommended fields:
```text
fracture_pressure
fracture_gradient
proposed_maip
aor_model_max_pressure
casing_pressure_rating
annulus_pressure_limit
operating_pressure_limit
```
All fields should be optional for the first implementation because real applications may provide partial evidence.
`MaipValidationFinding`
Recommended fields:
```text
finding_id
status
severity
message
recommended_action
supporting_values
```
Suggested statuses:
```text
pass
warning
fail
missing_evidence
```
`MaipValidationReport`
Recommended fields:
```text
overall_status
summary
findings
```
---
Initial Deterministic Rules
Rule 1: MAIP evidence must be present
If no proposed MAIP is found, emit:
```text
status: missing_evidence
severity: high
```
Reviewer message:
```text
The package does not provide a clear proposed Maximum Allowable Injection Pressure.
```
---
Rule 2: Fracture pressure or fracture gradient evidence must be present
If neither fracture pressure nor fracture gradient is found, emit:
```text
status: missing_evidence
severity: high
```
Reviewer message:
```text
The package does not provide clear fracture pressure or fracture gradient evidence needed to verify the proposed MAIP.
```
---
Rule 3: Proposed MAIP should not exceed 90% of fracture pressure
If both proposed MAIP and fracture pressure are available:
```text
proposed_maip <= 0.90 * fracture_pressure
```
If the rule fails, emit:
```text
status: fail
severity: critical
```
Reviewer message:
```text
The proposed MAIP exceeds 90% of the cited fracture pressure.
```
If the proposed MAIP is close to the limit, emit a warning:
```text
0.85 * fracture_pressure < proposed_maip <= 0.90 * fracture_pressure
```
Reviewer message:
```text
The proposed MAIP is below the 90% fracture-pressure limit but has a narrow operating margin.
```
---
Rule 4: AoR model pressure assumptions should not be lower than proposed operations
If both proposed MAIP and AoR model maximum pressure are available:
```text
proposed_maip <= aor_model_max_pressure
```
If the rule fails, emit:
```text
status: fail
severity: high
```
Reviewer message:
```text
The proposed MAIP exceeds the pressure constraint represented in the AoR model evidence.
```
---
Rule 5: Casing pressure rating should exceed proposed MAIP
If both proposed MAIP and casing pressure rating are available:
```text
proposed_maip < casing_pressure_rating
```
If the rule fails, emit:
```text
status: fail
severity: critical
```
Reviewer message:
```text
The proposed MAIP is not below the cited casing pressure rating.
```
---
Rule 6: Annulus pressure management evidence should be present
If annulus pressure or annulus management evidence is absent, emit:
```text
status: warning
severity: moderate
```
Reviewer message:
```text
The package does not provide clear annulus pressure management evidence linked to MAIP operations.
```
---
Rule 7: Operating margin should be documented
If operating margin evidence is absent, emit:
```text
status: warning
severity: moderate
```
Reviewer message:
```text
The package does not clearly document the operating margin between proposed injection pressure and the limiting pressure condition.
```
---
First Implementation Boundary
The first implementation should not attempt broad natural-language numeric extraction from every document.
Instead, use a staged approach:
```text
1. Define MAIP validation dataclasses.
2. Implement deterministic validation from structured inputs.
3. Add tests for passing, warning, failing, and missing-evidence scenarios.
4. Add package-review integration later.
5. Add numeric extraction later.
6. Add UI/export integration later.
```
This keeps the first implementation safe and testable.
---
Proposed File Layout
Initial implementation branch:
```text
review/maip_validation.py
tests/test_maip_validation.py
```
Later integration branches:
```text
review/package_review.py
review/report_export.py
ui/app.py
tests/test_package_maip_validation.py
tests/test_maip_validation_export.py
```
---
Proposed Future Branches
1. `feature/add-maip-validation-core`
Create the deterministic validator with structured inputs and unit tests.
2. `feature/add-maip-evidence-extraction`
Add targeted extraction for pressure values and source evidence from existing checklist findings and evidence locations.
3. `feature/add-maip-package-review-integration`
Attach MAIP validation results to package review output.
4. `feature/add-maip-export-support`
Add MAIP findings to Markdown package reports, final review packets, and deficiency exports.
5. `feature/add-maip-ui-panel`
Add a reviewer-facing MAIP validation panel to the Review Package tab.
---
Acceptance Criteria
A complete MAIP validation feature should:
```text
identify missing MAIP evidence
identify missing fracture-pressure evidence
verify proposed MAIP against 90% fracture pressure
compare proposed MAIP against AoR pressure assumptions
compare proposed MAIP against casing pressure rating
flag missing annulus-management evidence
flag missing operating-margin evidence
preserve source file and page evidence where available
emit deterministic severity-coded findings
include findings in package reports and final review packets
allow reviewer confirmation and notes
```
---
Non-Goals for the First Implementation
The first implementation should not:
```text
use an LLM to decide MAIP validity
replace checklist review
require the RAG index
require Ask Assistant
perform broad unvalidated numeric extraction
change existing package review behavior
```
---
Relationship to LLM Layer
The LLM narrative layer can later explain MAIP validation findings, but it should receive deterministic MAIP results as input.
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
+ reviewer notes
→ LLM-generated reviewer explanation
```
The LLM should improve readability, not replace the validator.
---
Current Decision
Build the MAIP validation feature before the LLM narrative layer.
Reason:
```text
The MAIP validator is deterministic.
It reconnects the branch to the original conceptual centerpiece.
It fits the current backend-first architecture.
It strengthens the product without depending on RAG or LLM readiness.
```