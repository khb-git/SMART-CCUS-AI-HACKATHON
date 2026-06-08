from review.temp_ingestion import TemporaryReviewChunk, TemporaryReviewDocument


def make_document(
    text: str,
    filename: str = "testing_monitoring_plan.pdf",
    content_type: str = "text",
):
    return TemporaryReviewDocument(
        original_filename=filename,
        file_extension=".pdf",
        chunks=[
            TemporaryReviewChunk(
                text=text,
                metadata={"content_type": content_type},
            )
        ],
    )


def finding_by_id(report):
    return {
        finding.item_id: finding
        for finding in report.findings
    }


def test_complete_testing_monitoring_table_evidence_is_present():
    from review.gap_analysis import analyze_document_against_checklist
    from review.schema import load_default_checklist

    document = make_document(
        (
            "Testing and Monitoring Plan.\n"
            "Table evidence | page 4 | table 1\n"
            "Table row: Parameter | Equipment | Frequency | Recording | Location\n"
            "Table row: Injection pressure | pressure transducer | continuous recording | SCADA | wellhead\n"
            "Table row: Injection rate | Coriolis meter | continuous recording | SCADA | injection line\n"
            "Table row: Annular pressure | pressure gauge | continuous recording | SCADA | casing annulus\n"
        )
    )

    checklist = load_default_checklist("testing_monitoring")
    report = analyze_document_against_checklist(document, checklist)
    findings = finding_by_id(report)

    assert findings["injection_pressure_monitoring"].status.value == "present"
    assert findings["injection_rate_monitoring"].status.value == "present"
    assert findings["annular_pressure_monitoring"].status.value == "present"

    assert findings["injection_pressure_monitoring"].matched_evidence_group_names
    assert findings["injection_rate_monitoring"].matched_evidence_group_names
    assert findings["annular_pressure_monitoring"].matched_evidence_group_names


def test_incomplete_testing_monitoring_evidence_stays_evidence_found():
    from review.gap_analysis import analyze_document_against_checklist
    from review.schema import load_default_checklist

    document = make_document(
        (
            "Testing and Monitoring Plan. "
            "The plan mentions injection pressure and annular pressure monitoring, "
            "but does not identify monitoring equipment, frequency, recording method, "
            "or measurement location."
        )
    )

    checklist = load_default_checklist("testing_monitoring")
    report = analyze_document_against_checklist(document, checklist)
    findings = finding_by_id(report)

    assert findings["injection_pressure_monitoring"].status.value == "evidence_found"
    assert findings["annular_pressure_monitoring"].status.value == "evidence_found"


def test_missing_testing_monitoring_evidence_stays_missing():
    from review.gap_analysis import analyze_document_against_checklist
    from review.schema import load_default_checklist

    document = make_document(
        (
            "Testing and Monitoring Plan. "
            "This section only discusses administrative contacts and schedule logistics."
        )
    )

    checklist = load_default_checklist("testing_monitoring")
    report = analyze_document_against_checklist(document, checklist)
    findings = finding_by_id(report)

    assert findings["injection_pressure_monitoring"].status.value == "missing"
    assert findings["injection_rate_monitoring"].status.value == "missing"
    assert findings["annular_pressure_monitoring"].status.value == "missing"


def test_complete_well_construction_evidence_is_present():
    from review.gap_analysis import analyze_document_against_checklist
    from review.schema import load_default_checklist

    document = make_document(
        (
            "Well Construction Plan. "
            "The casing program includes surface casing and long-string casing with "
            "depth, diameter, and grade. "
            "The cementing program describes cement, top of cement, centralizer use, "
            "and cement bond log verification. "
            "The tubing and packer section describes injection tubing, packer, annulus, "
            "and corrosion considerations."
        ),
        filename="well_construction_plan.pdf",
    )

    checklist = load_default_checklist("well_construction")
    report = analyze_document_against_checklist(document, checklist)
    findings = finding_by_id(report)

    assert findings["casing_program"].status.value == "present"
    assert findings["cementing_program"].status.value == "present"
    assert findings["tubing_packer"].status.value == "present"


def test_incomplete_well_construction_evidence_stays_evidence_found():
    from review.gap_analysis import analyze_document_against_checklist
    from review.schema import load_default_checklist

    document = make_document(
        (
            "Well Construction Plan. "
            "The document mentions casing and cement in general terms. "
            "Additional design details are not included in this excerpt."
        ),
        filename="well_construction_plan.pdf",
    )

    checklist = load_default_checklist("well_construction")
    report = analyze_document_against_checklist(document, checklist)
    findings = finding_by_id(report)

    assert findings["casing_program"].status.value == "evidence_found"
    assert findings["cementing_program"].status.value == "evidence_found"


def test_complete_financial_responsibility_evidence_is_present():
    from review.gap_analysis import analyze_document_against_checklist
    from review.schema import load_default_checklist

    document = make_document(
        (
            "Financial Responsibility Demonstration. "
            "The document provides a cost estimate and estimated cost for closure cost, "
            "corrective action cost, and PISC cost. "
            "The financial instrument is a letter of credit with a face value and "
            "coverage amount based on the cost estimate."
        ),
        filename="financial_responsibility.pdf",
    )

    checklist = load_default_checklist("financial_responsibility")
    report = analyze_document_against_checklist(document, checklist)
    findings = finding_by_id(report)

    assert findings["cost_estimate"].status.value == "present"
    assert findings["financial_instrument"].status.value == "present"
    assert findings["coverage_amount"].status.value == "present"


def test_aor_evidence_distinguishes_model_and_penetrations():
    from review.gap_analysis import analyze_document_against_checklist
    from review.schema import load_default_checklist

    document = make_document(
        (
            "Area of Review and Corrective Action Plan. "
            "The area of review is delineated using a computational model that predicts "
            "the plume and pressure front. "
            "The model domain and simulation assumptions are described. "
            "The plan includes a well inventory of legacy wells and artificial penetrations "
            "within the AoR."
        ),
        filename="aor_corrective_action.pdf",
    )

    checklist = load_default_checklist("aor_corrective_action")
    report = analyze_document_against_checklist(document, checklist)
    findings = finding_by_id(report)

    assert findings["aor_delineation"].status.value == "present"
    assert findings["computational_model"].status.value == "present"
    assert findings["penetrating_wells"].status.value == "present"


def test_supporting_pisc_timeframe_does_not_create_duplicate_pisc_plan():
    from review.package_review import review_document_package

    documents = [
        make_document(
            (
                "Post-Injection Site Care and Site Closure Plan. "
                "The plan describes PISC monitoring and non-endangerment demonstration."
            ),
            filename="Marquis_PISC_and_Site_Closure_Plan__36aa081feef7.pdf",
        ),
        make_document(
            (
                "Alternative PISC Timeframe. "
                "This document describes an alternative post-injection site care timeframe."
            ),
            filename="Marquis_Alternative_PISC_Timeframe__4b09b5518eb0.pdf",
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


def test_missing_required_main_document_still_controls_package_status():
    from review.package_review import review_document_package

    documents = [
        make_document(
            (
                "Alternative PISC Timeframe. "
                "This document describes an alternative post-injection site care timeframe."
            ),
            filename="Marquis_Alternative_PISC_Timeframe__4b09b5518eb0.pdf",
        ),
    ]

    report = review_document_package(
        documents,
        package_name="marquis_package",
        expected_plan_types=["pisc_site_closure"],
        required_plan_types=["pisc_site_closure"],
    )

    assert report.detected_plan_types == []
    assert report.supporting_documents == [
        "Marquis_Alternative_PISC_Timeframe__4b09b5518eb0.pdf"
    ]
    assert report.missing_required_plan_types == ["pisc_site_closure"]
    assert report.overall_status == "missing_required_documents"