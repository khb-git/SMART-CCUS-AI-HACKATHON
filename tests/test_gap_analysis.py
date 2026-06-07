from review.temp_ingestion import TemporaryReviewChunk, TemporaryReviewDocument


def make_document(text: str):
    return TemporaryReviewDocument(
        original_filename="testing_monitoring_plan.pdf",
        file_extension=".pdf",
        chunks=[
            TemporaryReviewChunk(
                text=text,
                metadata={"content_type": "text"},
            )
        ],
    )


def test_find_matching_terms_identifies_expected_terms():
    from review.gap_analysis import find_matching_terms

    text = (
        "Continuous recording devices will monitor wellhead injection pressure "
        "and flow rate using a Coriolis meter."
    )

    terms = [
        "continuous recording",
        "wellhead pressure",
        "flow rate",
        "Coriolis meter",
        "annular pressure",
    ]

    matched = find_matching_terms(text, terms)

    assert "continuous recording" in matched
    assert "flow rate" in matched
    assert "Coriolis meter" in matched
    assert "annular pressure" not in matched


def test_classify_item_status_present_for_strong_matches():
    from review.gap_analysis import GapStatus, classify_item_status
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("testing_monitoring")
    item = get_checklist_item(checklist, "injection_rate_monitoring")

    matched_terms = [
        "injection rate",
        "flow rate",
        "mass flowmeter",
        "Coriolis meter",
    ]

    assert classify_item_status(item, matched_terms) == GapStatus.PRESENT


def test_classify_item_status_missing_for_no_matches():
    from review.gap_analysis import GapStatus, classify_item_status
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("testing_monitoring")
    item = get_checklist_item(checklist, "annular_pressure_monitoring")

    assert classify_item_status(item, []) == GapStatus.MISSING


def test_analyze_checklist_item_returns_partial_finding():
    from review.gap_analysis import GapStatus, analyze_checklist_item
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("testing_monitoring")
    item = get_checklist_item(checklist, "calibration_schedule")

    text = "The pressure gauges will be calibrated annually."

    finding = analyze_checklist_item(text, item)

    assert finding.item_id == "calibration_schedule"
    assert finding.status in {GapStatus.PARTIAL, GapStatus.PRESENT}
    assert "calibrated annually" in finding.matched_terms
    assert finding.recommended_fix


def test_analyze_document_against_checklist_flags_missing_items():
    from review.gap_analysis import analyze_document_against_checklist
    from review.schema import load_default_checklist

    document = make_document(
        "Testing and Monitoring Plan. "
        "Continuous recording devices will monitor wellhead injection pressure, "
        "temperature, and flow rate. A Coriolis meter will measure mass flow rate."
    )

    checklist = load_default_checklist("testing_monitoring")
    report = analyze_document_against_checklist(document, checklist)

    assert report.document_name == "testing_monitoring_plan.pdf"
    assert report.plan_type == "testing_monitoring"
    assert report.findings
    assert report.overall_status in {
        "review_ready",
        "mostly_complete",
        "incomplete",
        "needs_revision",
    }

    finding_by_id = {finding.item_id: finding for finding in report.findings}

    assert finding_by_id["injection_pressure_monitoring"].status.value in {
        "present",
        "partial",
    }
    assert finding_by_id["injection_rate_monitoring"].status.value in {
        "present",
        "partial",
    }
    assert finding_by_id["annular_pressure_monitoring"].status.value == "missing"


def test_gap_analysis_report_to_dict_is_serializable():
    from review.gap_analysis import analyze_document_against_checklist
    from review.schema import load_default_checklist

    document = make_document(
        "Testing and Monitoring Plan. Injection pressure will be monitored continuously."
    )
    checklist = load_default_checklist("testing_monitoring")

    report = analyze_document_against_checklist(document, checklist)
    data = report.to_dict()

    assert data["document_name"] == "testing_monitoring_plan.pdf"
    assert data["plan_type"] == "testing_monitoring"
    assert data["checklist_id"] == "testing_monitoring_v1"
    assert data["summary"]
    assert data["findings"]
    assert data["findings"][0]["item_id"]
    assert data["findings"][0]["status"] in {
        "present",
        "partial",
        "missing",
        "unclear",
    }