def test_coverage_evidence_rows_for_display_formats_rows():
    from review.coverage_evidence_display import coverage_evidence_rows_for_display

    rows = coverage_evidence_rows_for_display(
        [
            {
                "plan_type": "financial_responsibility",
                "document_name": "Project_Narrative.pdf",
                "document_type": "project_narrative",
                "evidence_source": "text_evidence",
                "matched_terms": [
                    "financial assurance",
                    "cost estimate",
                    "plugging cost",
                ],
                "note": "Relevant text evidence found; reviewer confirmation recommended.",
            }
        ]
    )

    assert rows == [
        {
            "Package topic": "financial_responsibility",
            "Document": "Project_Narrative.pdf",
            "Primary type": "project_narrative",
            "Evidence source": "text_evidence",
            "Matched terms": "financial assurance, cost estimate, plugging cost",
            "Reviewer note": "Relevant text evidence found; reviewer confirmation recommended.",
        }
    ]


def test_coverage_evidence_rows_for_display_truncates_matched_terms():
    from review.coverage_evidence_display import coverage_evidence_rows_for_display

    rows = coverage_evidence_rows_for_display(
        [
            {
                "plan_type": "well_construction",
                "document_name": "Combined.pdf",
                "document_type": "project_narrative",
                "evidence_source": "filename, text_evidence",
                "matched_terms": [
                    "term1",
                    "term2",
                    "term3",
                ],
                "note": "Relevant text evidence found; reviewer confirmation recommended.",
            }
        ],
        max_terms=2,
    )

    assert rows[0]["Matched terms"] == "term1, term2, +1 more"