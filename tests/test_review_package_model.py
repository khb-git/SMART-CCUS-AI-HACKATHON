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

def test_review_package_counts_combined_document_coverage():
    from review.package_review import review_document_package

    documents = [
        make_document(
            "ADM_Narrative_AoR_Corrective_Action_Well_Construction.pdf",
            (
                "Class VI Permit Application Narrative. "
                "Area of Review and Corrective Action Plan. "
                "The plan evaluates legacy wells and artificial penetrations. "
                "Well Construction Plan. "
                "The well construction details include casing, cement, tubing, packer, "
                "and well schematic information."
            ),
        )
    ]

    report = review_document_package(
        documents,
        package_name="adm_combined_package",
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

    assert report.missing_required_plan_types == []
    assert report.missing_expected_plan_types == []
    assert "project_narrative" in report.detected_plan_types
    assert "aor_corrective_action" in report.detected_plan_types
    assert "well_construction" in report.detected_plan_types

    document_review = report.document_reviews[0]

    assert document_review.is_combined_document is True
    assert "project_narrative" in document_review.covered_plan_types
    assert "aor_corrective_action" in document_review.covered_plan_types
    assert "well_construction" in document_review.covered_plan_types


def test_review_package_still_detects_duplicate_plan_types_with_combined_documents():
    from review.package_review import review_document_package

    documents = [
        make_document(
            "ADM_Combined_Narrative_AoR_Well_Construction.pdf",
            (
                "Class VI Permit Application Narrative. "
                "Area of Review and Corrective Action Plan. "
                "Well Construction Plan with casing, cement, tubing, and packer."
            ),
        ),
        make_document(
            "Standalone_Well_Construction_Plan.pdf",
            (
                "Well Construction Plan. The document describes casing, cementing, "
                "tubing, packer configuration, and well schematic details."
            ),
        ),
    ]

    report = review_document_package(
        documents,
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

    assert "well_construction" in report.duplicate_plan_types
    assert "well_construction" in report.detected_plan_types

def test_review_package_identifies_supporting_pisc_alternative_timeframe():
    from review.package_review import review_document_package

    documents = [
        make_document(
            "Marquis_PISC_and_Site_Closure_Plan__36aa081feef7.pdf",
            (
                "Post-Injection Site Care and Site Closure Plan. "
                "The plan describes PISC monitoring and non-endangerment demonstration."
            ),
        ),
        make_document(
            "Marquis_Alternative_PISC_Timeframe__4b09b5518eb0.pdf",
            (
                "Alternative PISC Timeframe. "
                "This document describes an alternative post-injection site care timeframe."
            ),
        ),
    ]

    report = review_document_package(
        documents,
        package_name="marquis_package",
        expected_plan_types=["pisc_site_closure"],
        required_plan_types=["pisc_site_closure"],
    )

    assert report.detected_plan_types == ["pisc_site_closure"]
    assert report.duplicate_plan_types == []
    assert report.supporting_documents == [
        "Marquis_Alternative_PISC_Timeframe__4b09b5518eb0.pdf"
    ]
    assert "Supporting documents: 1" in report.summary

    supporting_review = [
        review
        for review in report.document_reviews
        if review.document_name == "Marquis_Alternative_PISC_Timeframe__4b09b5518eb0.pdf"
    ][0]

    assert supporting_review.document_role == "supporting"
    assert supporting_review.supporting_document_type == (
        "supporting_pisc_alternative_timeframe"
    )
    assert supporting_review.report is None
    assert "Supporting document detected" in supporting_review.error


def test_review_package_report_to_dict_includes_supporting_documents():
    from review.package_review import review_document_package

    documents = [
        make_document(
            "Marquis_Alternative_PISC_Timeframe__4b09b5518eb0.pdf",
            "Alternative PISC Timeframe document.",
        )
    ]

    report = review_document_package(
        documents,
        package_name="marquis_package",
        expected_plan_types=[],
        required_plan_types=[],
    )

    data = report.to_dict()

    assert data["supporting_documents"] == [
        "Marquis_Alternative_PISC_Timeframe__4b09b5518eb0.pdf"
    ]
    assert data["document_reviews"][0]["document_role"] == "supporting"
    assert data["document_reviews"][0]["supporting_document_type"] == (
        "supporting_pisc_alternative_timeframe"
    )

def test_duplicate_detection_counts_primary_documents_only():
    from review.package_review import (
        PackageDocumentReview,
        find_duplicate_plan_types,
    )

    reviews = [
        PackageDocumentReview(
            document_name="Narrative.pdf",
            document_type="project_narrative",
            classification_confidence="high",
            classification={},
            covered_plan_types=[
                "project_narrative",
                "aor_corrective_action",
                "testing_monitoring",
            ],
            document_role="main",
        ),
        PackageDocumentReview(
            document_name="AoR.pdf",
            document_type="aor_corrective_action",
            classification_confidence="high",
            classification={},
            covered_plan_types=[
                "aor_corrective_action",
                "testing_monitoring",
            ],
            document_role="main",
        ),
    ]

    assert find_duplicate_plan_types(reviews) == []


def test_duplicate_detection_flags_repeated_primary_documents():
    from review.package_review import (
        PackageDocumentReview,
        find_duplicate_plan_types,
    )

    reviews = [
        PackageDocumentReview(
            document_name="Testing_and_Monitoring_1.pdf",
            document_type="testing_monitoring",
            classification_confidence="high",
            classification={},
            covered_plan_types=["testing_monitoring"],
            document_role="main",
        ),
        PackageDocumentReview(
            document_name="Testing_and_Monitoring_2.pdf",
            document_type="testing_monitoring",
            classification_confidence="high",
            classification={},
            covered_plan_types=["testing_monitoring"],
            document_role="main",
        ),
    ]

    assert find_duplicate_plan_types(reviews) == ["testing_monitoring"]


def test_filename_audit_overrides_cost_estimates_primary_type():
    from review.package_review import review_single_package_document

    document = make_document(
        "Marquis_Cost_Estimates.pdf",
        (
            "Post-injection site care cost estimate. "
            "This document includes cost estimates for plugging, corrective action, "
            "site closure, emergency response, and financial assurance coverage."
        ),
    )

    review = review_single_package_document(document)

    assert review.document_type == "financial_responsibility"
    assert review.classification["document_type"] == "financial_responsibility"
    assert "financial_responsibility" in review.checklist_reports


def test_filename_audit_overrides_narrative_primary_type():
    from review.package_review import review_single_package_document

    document = make_document(
        "Marquis_Narrative.pdf",
        (
            "Class VI permit application narrative. "
            "The application describes the project, facility information, "
            "injection project, location, and applicant."
        ),
    )

    review = review_single_package_document(document)

    assert review.document_type == "project_narrative"
    assert review.classification["document_type"] == "project_narrative"
    assert "project_narrative" in review.checklist_reports


def test_filename_audit_overrides_testing_monitoring_primary_type():
    from review.package_review import review_single_package_document

    document = make_document(
        "Marquis_Testing_and_Monitoring_Plan.pdf",
        (
            "Testing and Monitoring Plan. "
            "The plan describes injection pressure monitoring, flow rate, "
            "annular pressure, groundwater monitoring, SCADA, and reporting."
        ),
    )

    review = review_single_package_document(document)

    assert review.document_type == "testing_monitoring"
    assert review.classification["document_type"] == "testing_monitoring"
    assert "testing_monitoring" in review.checklist_reports

def test_filename_audit_override_limits_review_to_primary_type():
    from review.package_review import review_single_package_document

    document = make_document(
        "Marquis_Narrative.pdf",
        (
            "Post-injection site care and site closure plan references appear here, "
            "along with testing and monitoring, well construction, and AoR references. "
            "This file is the project narrative by filename."
        ),
    )

    review = review_single_package_document(document)

    assert review.document_type == "project_narrative"
    assert review.covered_plan_types == ["project_narrative"]
    assert list(review.checklist_reports) == ["project_narrative"]
    assert review.is_combined_document is False

def test_filename_audit_preserves_explicit_combined_filename_coverage():
    from review.package_review import review_single_package_document

    document = make_document(
        "ADM_Narrative_AoR_Corrective_Action_Well_Construction.pdf",
        (
            "Class VI Permit Application Narrative. "
            "Area of Review and Corrective Action Plan. "
            "The plan evaluates legacy wells and artificial penetrations. "
            "Well Construction Plan. "
            "The well construction details include casing, cement, tubing, packer, "
            "and well schematic information."
        ),
    )

    review = review_single_package_document(document)

    assert review.is_combined_document is True
    assert "project_narrative" in review.covered_plan_types
    assert "aor_corrective_action" in review.covered_plan_types
    assert "well_construction" in review.covered_plan_types

def test_site_geologic_and_site_operating_are_not_required_standalone_documents():
    from review.package_review import review_document_package

    documents = [
        make_document(
            "Marquis_Narrative.pdf",
            "Class VI project narrative for CO2 injection and storage.",
        ),
        make_document(
            "Marquis_AoR_and_Corrective_Action_Plan.pdf",
            "Area of Review and Corrective Action Plan with computational model.",
        ),
        make_document(
            "Marquis_Cost_Estimates.pdf",
            "Cost estimate and financial assurance coverage.",
        ),
        make_document(
            "Marquis_Well_Construction_Plan.pdf",
            "Well construction plan with casing, cement, tubing, and packer.",
        ),
        make_document(
            "Marquis_Testing_and_Monitoring_Plan.pdf",
            "Testing and monitoring plan with pressure, flow, and reporting.",
        ),
        make_document(
            "Marquis_Injection_Well_Plugging_Plan.pdf",
            "Injection well plugging plan with cement plugs and verification.",
        ),
        make_document(
            "Marquis_PISC_and_Site_Closure_Plan.pdf",
            "Post-injection site care and site closure plan.",
        ),
        make_document(
            "Marquis_ERRP_0.pdf",
            "Emergency and remedial response plan.",
        ),
    ]

    report = review_document_package(documents, package_name="marquis_package")

    assert "site_geologic_characterization" not in report.required_plan_types
    assert "site_operating" not in report.required_plan_types
    assert "site_geologic_characterization" not in report.expected_plan_types
    assert "site_operating" not in report.expected_plan_types
    assert "site_geologic_characterization" not in report.missing_required_plan_types
    assert "site_operating" not in report.missing_required_plan_types
    assert "site_geologic_characterization" not in report.missing_expected_plan_types
    assert "site_operating" not in report.missing_expected_plan_types

def test_package_coverage_credits_explicit_adm_combined_filename():
    from review.package_review import review_document_package

    documents = [
        make_document(
            "ADM_Narrative+AoR_and_Corrective_Action_Plan+Well_Construction_Plan.pdf",
            (
                "Class VI Permit Application Narrative. "
                "Area of Review and Corrective Action Plan. "
                "Section 6. Well Construction Details. "
                "The casing specifications describe surface casing, long string casing, "
                "cement, tubing, packer, and well schematic information."
            ),
        )
    ]

    report = review_document_package(
        documents,
        package_name="adm_combined_package",
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

    assert report.missing_required_plan_types == []
    assert report.missing_expected_plan_types == []
    assert "project_narrative" in report.detected_plan_types
    assert "aor_corrective_action" in report.detected_plan_types
    assert "well_construction" in report.detected_plan_types

    review = report.document_reviews[0]

    assert "project_narrative" in review.coverage_plan_types
    assert "aor_corrective_action" in review.coverage_plan_types
    assert "well_construction" in review.coverage_plan_types


def test_package_coverage_credits_financial_responsibility_inside_narrative():
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

    assert report.missing_required_plan_types == []
    assert report.missing_expected_plan_types == []
    assert "financial_responsibility" in report.detected_plan_types

    review = report.document_reviews[0]

    assert review.document_type == "project_narrative"
    assert review.covered_plan_types == ["project_narrative"]
    assert "financial_responsibility" in review.coverage_plan_types


def test_package_coverage_credits_wabash_well_construction_evidence_in_plugging_plan():
    from review.package_review import review_document_package

    documents = [
        make_document(
            "Wabash_Injection_Well_Plugging_Plan.pdf",
            (
                "Injection Well Plugging Plan. "
                "The procedure discusses tubing, packer retrieval, casing integrity, "
                "cement bond log CBL, USIT logs, cement formulation, and cementing operations."
            ),
        )
    ]

    report = review_document_package(
        documents,
        package_name="wabash_package",
        expected_plan_types=["injection_well_plugging", "well_construction"],
        required_plan_types=["injection_well_plugging", "well_construction"],
    )

    assert report.missing_required_plan_types == []
    assert report.missing_expected_plan_types == []
    assert "injection_well_plugging" in report.detected_plan_types
    assert "well_construction" in report.detected_plan_types

    review = report.document_reviews[0]

    assert review.document_type == "injection_well_plugging"
    assert review.covered_plan_types == ["injection_well_plugging"]
    assert "well_construction" in review.coverage_plan_types

def test_package_review_adds_cross_document_context_for_missing_findings():
    from review.package_review import review_document_package

    documents = [
        make_document(
            "Demo_PISC_and_Site_Closure_Plan.pdf",
            (
                "Post-Injection Site Care and Site Closure Plan. "
                "The plan describes PISC monitoring and non-endangerment demonstration."
            ),
        ),
        make_document(
            "Demo_Cost_Estimates.pdf",
            (
                "Financial Responsibility cost estimates. "
                "This document includes financial assurance, cost estimate, "
                "coverage amount, plugging cost, PISC cost, and site closure cost."
            ),
        ),
    ]

    report = review_document_package(
        documents,
        package_name="demo_package",
        expected_plan_types=["pisc_site_closure", "financial_responsibility"],
        required_plan_types=["pisc_site_closure", "financial_responsibility"],
    )

    pisc_review = [
        review
        for review in report.document_reviews
        if review.document_name == "Demo_PISC_and_Site_Closure_Plan.pdf"
    ][0]

    pisc_report = pisc_review.checklist_reports["pisc_site_closure"]
    findings = pisc_report["findings"]

    related_findings = [
        finding
        for finding in findings
        if finding.get("related_package_evidence")
    ]

    assert related_findings

    related_evidence = related_findings[0]["related_package_evidence"]

    assert related_evidence[0]["document_name"] == "Demo_Cost_Estimates.pdf"
    assert related_evidence[0]["evidence_source"] == "cross_document_text"
    assert related_evidence[0]["matched_terms"]

def test_short_pisc_filename_overrides_aor_text_primary_type():
    from review.package_review import review_document_package

    documents = [
        make_document(
            "HGCS_Vervain_AoR_and_Corrective_Action_Plan.pdf",
            (
                "Area of Review and Corrective Action Plan. "
                "The plan describes AoR delineation, corrective action, legacy wells, "
                "and artificial penetrations."
            ),
        ),
        make_document(
            "HGCS_Vervain_PISC.pdf",
            (
                "Post-Injection Site Care Plan. "
                "This document references the Area of Review and corrective action process, "
                "including AoR reevaluation and corrective action updates. "
                "It describes PISC monitoring and non-endangerment demonstration."
            ),
        ),
    ]

    report = review_document_package(
        documents,
        package_name="heartland_vervain_package",
        expected_plan_types=[
            "aor_corrective_action",
            "pisc_site_closure",
        ],
        required_plan_types=[
            "aor_corrective_action",
            "pisc_site_closure",
        ],
    )

    assert report.missing_required_plan_types == []
    assert report.duplicate_plan_types == []

    pisc_review = [
        review
        for review in report.document_reviews
        if review.document_name == "HGCS_Vervain_PISC.pdf"
    ][0]

    assert pisc_review.document_type == "pisc_site_closure"
    assert pisc_review.covered_plan_types == ["pisc_site_closure"]
    assert "aor_corrective_action" in pisc_review.coverage_plan_types