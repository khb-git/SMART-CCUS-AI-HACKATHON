# Real Document Validation Workflow

This workflow records validation observations from real Class VI-style review
documents without committing real permit documents or sensitive project files to
the repository.

## Purpose

Use local real-document runs to identify:

- Correct checklist classifications
- False positives
- False negatives
- Missing evidence groups
- OCR behavior
- Redacted OCR behavior
- Page-location issues
- Reviewer follow-up items
- Known limitations

## Repository hygiene

Do not commit:

- Real permit PDFs
- Redacted or unredacted application packages
- Applicant-specific confidential information
- Generated review outputs containing sensitive excerpts
- Screenshots from confidential documents

Commit only sanitized summaries, templates, and regression tests.

## Recommended validation sequence

1. Pull latest `develop`.
2. Run full tests.
3. Run one document through `/review-document` or local review helpers.
4. Run a full package through `/review-package`.
5. Export Markdown review output.
6. Check each finding against the source document.
7. Record sanitized validation notes in `docs/validation/`.
8. Convert repeatable issues into synthetic regression tests.

## What to record

For each validation run, record:

- Document type reviewed
- Expected checklist type
- Actual detected type
- Overall status
- Items incorrectly marked present
- Items incorrectly marked missing
- Items incorrectly marked evidence found
- OCR evidence behavior
- Redacted OCR behavior
- Page-number accuracy
- Source-label accuracy
- Reviewer decision
- Follow-up action

## Status labels

Use these labels consistently:

- `pass`
- `needs_review`
- `false_positive`
- `false_negative`
- `overcredited`
- `undercredited`
- `ocr_issue`
- `page_location_issue`
- `classification_issue`
- `known_limitation`

## Safety boundary

The validation log should describe behavior without copying sensitive source
content. Use short sanitized summaries instead of full excerpts.

Example:

```text
Good: OCR detected a redacted confidentiality marker on page 3 and labeled the
evidence as redacted_image_ocr.

Avoid: Copying full confidential applicant text from the source document.
```

## When to create regression tests

Create a synthetic regression test when a real-document validation issue is:

- Repeatable
- Rule-based
- Checklist-related
- OCR-label-related
- Page-location-related
- Export-format-related

Do not create regression tests using real document text. Use sanitized synthetic
text that captures the same failure pattern.