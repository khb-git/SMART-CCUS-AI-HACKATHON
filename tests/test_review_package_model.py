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


def test_review_document_package_detects_missing_required_documents():
    from review.package_review import review_document_package

    documents = [
        make_document(
            "ADM_Testing_and_Monitoring_Plan.pdf",
            (
                "Testing and Monitoring Plan. The plan describes injection pressure "
                "monitoring, injection rate monitoring, and plume and pressure front tracking."
            ),
        ),
        make_document(
            "ADM_Emergency_and_Remedial_Response_Plan.pdf",
            (
                "Emergency and Remedial Response Plan. The plan describes emergency "
                "response triggers, notification procedures, shut-in procedures, and remedial actions."
            ),
        ),
    ]

    report = review_document_package(documents)

    assert report.package_name == "uploaded_package"
    assert "testing_monitoring" in report.detected_plan_types
    assert "emergency_remedial_response" in report.detected_plan_types
    assert "well_construction" in report.missing_required_plan_types
    assert report.overall_status == "missing_required_documents"
    assert report.document_reviews


def test_review_document_package_can_use_custom_required_plan_types():
    from review.package_review import review_document_package

    documents = [
        make_document(
            "ADM_Testing_and_Monitoring_Plan.pdf",
            "Testing and Monitoring Plan. Injection pressure monitoring and flow rate monitoring.",
        ),
    ]

    report = review_document_package(
        documents,
        package_name="test_package",
        expected_plan_types=["testing_monitoring"],
        required_plan_types=["testing_monitoring"],
    )

    assert report.package_name == "test_package"
    assert report.missing_required_plan_types == []
    assert report.missing_expected_plan_types == []
    assert report.overall_status in {
        "package_review_ready",
        "mostly_complete",
        "incomplete",
        "needs_revision",
    }


def test_review_document_package_identifies_unknown_documents():
    from review.package_review import review_document_package

    documents = [
        make_document(
            "meeting_notes.pdf",
            "These are unrelated meeting notes about travel and scheduling.",
        ),
    ]

    report = review_document_package(
        documents,
        expected_plan_types=[],
        required_plan_types=[],
    )

    assert report.unknown_documents == ["meeting_notes.pdf"]
    assert report.overall_status == "needs_review"
    assert report.document_reviews[0].document_type == "unknown"
    assert report.document_reviews[0].error


def test_review_document_package_identifies_duplicate_plan_types():
    from review.package_review import review_document_package

    documents = [
        make_document(
            "ADM_Testing_and_Monitoring_Plan.pdf",
            "Testing and Monitoring Plan. Injection pressure monitoring.",
        ),
        make_document(
            "Backup_Testing_Monitoring.pdf",
            "Testing and Monitoring Plan. Flow rate monitoring.",
        ),
    ]

    report = review_document_package(
        documents,
        expected_plan_types=["testing_monitoring"],
        required_plan_types=["testing_monitoring"],
    )

    assert report.duplicate_plan_types == ["testing_monitoring"]


def test_review_package_report_to_dict_is_serializable():
    from review.package_review import review_document_package

    documents = [
        make_document(
            "ADM_PISC_and_Site_Closure_Plan.pdf",
            (
                "Post-Injection Site Care and Site Closure Plan. The plan describes "
                "PISC monitoring and non-endangerment demonstration."
            ),
        )
    ]

    report = review_document_package(
        documents,
        package_name="adm_package",
        expected_plan_types=["pisc_site_closure"],
        required_plan_types=["pisc_site_closure"],
    )

    data = report.to_dict()

    assert data["package_name"] == "adm_package"
    assert data["overall_status"]
    assert data["summary"]
    assert data["expected_plan_types"] == ["pisc_site_closure"]
    assert data["required_plan_types"] == ["pisc_site_closure"]
    assert data["document_reviews"]
    assert data["document_reviews"][0]["document_name"] == (
        "ADM_PISC_and_Site_Closure_Plan.pdf"
    )


def test_review_single_package_document_returns_report_for_known_type():
    from review.package_review import review_single_package_document

    document = make_document(
        "ADM_Well_Construction_Plan.pdf",
        (
            "Well Construction Plan. The document describes casing, cementing, "
            "tubing, packer configuration, and well schematic details."
        ),
    )

    review = review_single_package_document(document)

    assert review.document_name == "ADM_Well_Construction_Plan.pdf"
    assert review.document_type == "well_construction"
    assert review.classification_confidence in {"medium", "high"}
    assert review.report
    assert not review.error