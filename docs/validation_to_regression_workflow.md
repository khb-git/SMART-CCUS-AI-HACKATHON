# Validation to Regression Workflow

This workflow converts sanitized real-document validation findings into synthetic
regression-test candidates.

## Purpose

Real document validation should improve the deterministic reviewer without
committing real permit documents or sensitive source excerpts.

The workflow is:

1. Run the reviewer on local real documents.
2. Record sanitized findings in `docs/validation/`.
3. Label each finding consistently.
4. Convert repeatable issues into regression candidates.
5. Implement synthetic tests that reproduce the issue pattern without using real
   source text.

## Regression-worthy labels

The following labels should usually become regression-test candidates:

- `false_positive`
- `false_negative`
- `overcredited`
- `undercredited`
- `ocr_issue`
- `page_location_issue`
- `classification_issue`

The following labels are useful for documentation but may not need tests:

- `pass`
- `needs_review`
- `known_limitation`

## Safety

Do not use real permit text in regression tests.

Use short synthetic examples that preserve the pattern of the issue.

Example:

```text
Real validation issue:
The system marked a financial instrument present even though the source did not
say the letter of credit was payable to the Director.

Synthetic regression test:
"The financial instrument is a letter of credit with a face value."

Expected result:
`evidence_found`, not `present`, because payable-to evidence is missing.
```

## Candidate review checklist

Before writing a test, confirm:

- The issue is repeatable.
- The issue is rule-based.
- The issue can be reproduced with synthetic text.
- The expected behavior is clear.
- The test does not copy sensitive source content.