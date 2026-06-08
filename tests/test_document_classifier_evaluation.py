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


CLASSIFIER_EVALUATION_CASES = [
    {
        "filename": "ADM_Testing_and_Monitoring_Plan.pdf",
        "text": (
            "Testing and Monitoring Plan. The plan describes injection pressure "
            "monitoring, injection rate monitoring, annular pressure, monitoring "
            "frequency, and plume and pressure front tracking."
        ),
        "expected": "testing_monitoring",
    },
    {
        "filename": "ADM_Pre_Operational_Testing_Plan.pdf",
        "text": (
            "Pre-Operational Testing Plan. The plan describes formation testing, "
            "mechanical integrity testing, baseline monitoring, and logging before injection."
        ),
        "expected": "pre_operational_testing",
    },
    {
        "filename": "ADM_PISC_and_Site_Closure_Plan.pdf",
        "text": (
            "Post-Injection Site Care and Site Closure Plan. The plan describes "
            "the PISC period, post-injection monitoring, site closure activities, "
            "and non-endangerment demonstration."
        ),
        "expected": "pisc_site_closure",
    },
    {
        "filename": "ADM_Emergency_and_Remedial_Response_Plan.pdf",
        "text": (
            "Emergency and Remedial Response Plan. The plan describes emergency "
            "response triggers, notification procedures, shut-in procedures, and remedial actions."
        ),
        "expected": "emergency_remedial_response",
    },
    {
        "filename": "ADM_Well_Construction_Plan.pdf",
        "text": (
            "Well Construction Plan. The document describes casing, cementing, "
            "injection tubing, packer configuration, and well schematic details."
        ),
        "expected": "well_construction",
    },
    {
        "filename": "ADM_Area_of_Review_and_Corrective_Action_Plan.pdf",
        "text": (
            "Area of Review and Corrective Action Plan. The plan describes AoR "
            "delineation, computational model results, legacy wells, artificial "
            "penetrations, and corrective action."
        ),
        "expected": "aor_corrective_action",
    },
    {
        "filename": "ADM_Financial_Responsibility_Demonstration.pdf",
        "text": (
            "Financial Responsibility Demonstration. The document includes cost "
            "estimate information, financial assurance, letter of credit, and surety bond details."
        ),
        "expected": "financial_responsibility",
    },
    {
        "filename": "ADM_Site_Operating_Plan.pdf",
        "text": (
            "Site Operating Plan. The plan describes operating parameters, maximum "
            "injection pressure, injection rate, alarm setpoints, and shutoff systems."
        ),
        "expected": "site_operating",
    },
    {
        "filename": "ADM_Site_Geologic_Characterization.pdf",
        "text": (
            "Site Geologic Characterization. The document describes the injection zone, "
            "confining zone, faults, fractures, hydrogeology, USDWs, and geochemical data."
        ),
        "expected": "site_geologic_characterization",
    },
    {
        "filename": "ADM_Injection_Well_Plugging_Plan.pdf",
        "text": (
            "Injection Well Plugging Plan. The plan describes plugging methods, cement plugs, "
            "plugging depths, pre-plugging conditions, and plugging verification."
        ),
        "expected": "injection_well_plugging",
    },
    {
        "filename": "ADM_Project_Narrative.pdf",
        "text": (
            "Project Narrative. The application narrative describes the project description, "
            "applicant information, injection project, facility information, and site location."
        ),
        "expected": "project_narrative",
    },
]


def test_classifier_recognizes_supported_document_types():
    from review.document_classifier import classify_review_document

    for case in CLASSIFIER_EVALUATION_CASES:
        document = make_document(
            filename=case["filename"],
            text=case["text"],
        )

        classification = classify_review_document(document)

        assert classification.document_type == case["expected"], case
        assert classification.confidence in {"medium", "high"}, case
        assert classification.matched_terms, case


def test_classifier_outputs_have_matching_checklists():
    from review.document_classifier import classify_review_document
    from review.schema import load_default_checklist

    for case in CLASSIFIER_EVALUATION_CASES:
        document = make_document(
            filename=case["filename"],
            text=case["text"],
        )

        classification = classify_review_document(document)

        assert classification.document_type == case["expected"], case

        checklist = load_default_checklist(classification.document_type)

        assert checklist.plan_type == classification.document_type


def test_classifier_recognizes_common_abbreviations():
    from review.document_classifier import classify_review_document

    cases = [
        (
            "ADM_ERR_Plan.pdf",
            "ERR Plan. Emergency response and remedial response procedures.",
            "emergency_remedial_response",
        ),
        (
            "ADM_PISC_SC_Plan.pdf",
            "PISC and Site Closure Plan. Post-injection monitoring and non-endangerment.",
            "pisc_site_closure",
        ),
        (
            "ADM_AoR_CA_Plan.pdf",
            "AoR and Corrective Action Plan. Corrective action for legacy wells.",
            "aor_corrective_action",
        ),
        (
            "ADM_FR_Demonstration.pdf",
            "FR Demonstration. Financial responsibility and cost estimate.",
            "financial_responsibility",
        ),
    ]

    for filename, text, expected in cases:
        document = make_document(filename=filename, text=text)
        classification = classify_review_document(document)

        assert classification.document_type == expected
        assert classification.confidence in {"medium", "high"}


def test_classifier_returns_unknown_for_unrelated_document():
    from review.document_classifier import classify_review_document

    document = make_document(
        filename="meeting_notes.pdf",
        text="These are meeting notes about lunch, travel, and scheduling.",
    )

    classification = classify_review_document(document)

    assert classification.document_type == "unknown"
    assert classification.confidence == "unknown"
    assert classification.matched_terms == []