# OCR Validation Workflow

This workflow validates OCR behavior on local review documents without committing
real permit files to the repository.

## Purpose

Confirm that image-derived evidence is:

- Extracted only as visible OCR text
- Labeled as `image_ocr` or `redacted_image_ocr`
- Page-located when possible
- Shown with reviewer notes
- Not used to infer hidden redacted content

## Run validation

```powershell
python scripts/validate_ocr_review_ingestion.py "C:\path\to\review.pdf"
```

Force OCR on all pages:

```powershell
python scripts/validate_ocr_review_ingestion.py "C:\path\to\review.pdf" --force-ocr
```

Disable OCR for comparison:

```powershell
python scripts/validate_ocr_review_ingestion.py "C:\path\to\review.pdf" --disable-ocr
```

Adjust the low-text threshold for OCR:

```powershell
python scripts/validate_ocr_review_ingestion.py "C:\path\to\review.pdf" --ocr-min-text-chars 250
```

## Expected behavior

Redacted pages should produce `redacted_image_ocr` chunks when OCR detects
redaction or confidentiality markers.

Unredacted image-only pages should produce `image_ocr` chunks when visible text is
detected.

Pages with enough selectable text are skipped by default unless `--force-ocr` is
used.

## Safety boundaries

The backend must not infer hidden content behind redactions.

OCR-derived evidence should be treated as reviewer-supporting evidence, not a
final compliance determination.

A reviewer should confirm OCR-derived evidence against the source page before
using it to satisfy a checklist item.

## Example output

```text
OCR validation summary
======================
File: C:\path\to\review.pdf
Total chunks: 14
OCR chunks: 2
Redacted OCR chunks: 1

OCR chunk 1
----------------------------------------
Page: 3
Source type: redacted_image_ocr
Redaction detected: True
OCR confidence: Low
Reviewer note: OCR detected redaction/confidentiality markers. The backend cannot inspect or infer hidden content.
Excerpt: Sensitive, Confidential, or Privileged Information
```

## Repository hygiene

Do not commit real permit packages, redacted PDFs, unredacted PDFs, or generated
validation outputs containing project-sensitive content.

Commit only:

- `scripts/validate_ocr_review_ingestion.py`
- `tests/test_ocr_validation_runner.py`
- `docs/ocr_validation_workflow.md`