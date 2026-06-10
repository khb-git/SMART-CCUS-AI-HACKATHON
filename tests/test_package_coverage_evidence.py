from review.temp_ingestion import TemporaryReviewChunk, TemporaryReviewDocument


def make_document(filename: str, text: str):
    return TemporaryReviewDocument(
        original_filename=filename,
        file_extension=".pdf",
        chunks=[
            TemporaryReviewChunk(
                text=text,
                metadata={"content_type": "text"},
            )
        ],
    )


def test_package_report_includes_coverage_evidence_rows():
    from review.package_review import review_document_package

    documents = [
        make_document(
            "Heartland_Project_Narrative.pdf",
            (
                "Class VI Permit Application Narrative. "
                "The application includes project description, facility information, "
                "and applicant details. "
                "The narrative also includes financial assurance information, "
                "cost estimates, plugging cost, corrective action cost, and PISC cost."
            ),
        )
    ]

    report = review_document_package(
        documents,
        package_name="heartland_package",
        expected_plan_types=["project_narrative", "financial_responsibility"],
        required_plan_types=["project_narrative", "financial_responsibility"],
    )

    assert report.coverage_evidence

    financial_evidence = [
        row
        for row in report.coverage_evidence
        if row.plan_type == "financial_responsibility"
    ]

    assert financial_evidence
    assert financial_evidence[0].document_name == "Heartland_Project_Narrative.pdf"
    assert "text_evidence" in financial_evidence[0].evidence_source
    assert "financial assurance" in financial_evidence[0].matched_terms


def test_package_report_to_dict_includes_coverage_evidence():
    from review.package_review import review_document_package

    documents = [
        make_document(
            "ADM_Narrative+AoR_and_Corrective_Action_Plan+Well_Construction_Plan.pdf",
            (
                "Class VI Permit Application Narrative. "
                "Area of Review and Corrective Action Plan. "
                "Well Construction Plan. "
                "The well construction details include casing, cement, tubing, packer, "
                "and well schematic information."
            ),
        )
    ]

    report = review_document_package(
        documents,
        package_name="adm_package",
        expected_plan_types=[
            "project_narrative",
            "aor_corrective_action",
            "well_construction",
        ],
        required_plan_types=[
            "project_narrative",
            "aor_corrective_action",
            "well_construction",
        ],
    )

    data = report.to_dict()

    assert "coverage_evidence" in data
    assert data["coverage_evidence"]

    evidence_plan_types = {
        row["plan_type"]
        for row in data["coverage_evidence"]
    }

    assert "project_narrative" in evidence_plan_types
    assert "aor_corrective_action" in evidence_plan_types
    assert "well_construction" in evidence_plan_types