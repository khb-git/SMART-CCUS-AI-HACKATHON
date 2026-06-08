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
        "evidence_found",
    }
    assert finding_by_id["injection_rate_monitoring"].status.value in {
        "present",
        "evidence_found",
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
        "evidence_found",
        "missing",
        "unclear",
    }

def test_clean_excerpt_text_removes_section_context_and_shortens():
    from review.gap_analysis import clean_excerpt_text

    text = (
        "Section context: 9.6 Testing and monitoring plan QASP "
        + "Injection pressure and flow rate will be reported. " * 30
    )

    cleaned = clean_excerpt_text(text, max_length=160)

    assert "Section context:" not in cleaned
    assert len(cleaned) <= 163
    assert cleaned.endswith("...")


def test_supporting_excerpts_are_short_and_clean():
    from review.gap_analysis import find_supporting_excerpts

    text = (
        "Section context: 9.6 Testing and monitoring plan QASP "
        "The injection pressure, injection volume and flow rate, annulus fluid level, "
        "annulus pressure, and temperature shall be submitted on one or more graphs, "
        "using contrasting symbols or colors, or in another manner approved by the Director. "
        "Additional unrelated material follows. " * 10
    )

    excerpts = find_supporting_excerpts(
        text=text,
        matched_terms=["injection pressure", "flow rate"],
        max_excerpts=1,
    )

    assert len(excerpts) == 1
    assert "Section context:" not in excerpts[0]
    assert len(excerpts[0]) <= 453


def test_present_status_requires_stronger_matches():
    from review.gap_analysis import GapStatus, classify_item_status
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("testing_monitoring")
    item = get_checklist_item(checklist, "monitoring_equipment")

    weak_matches = ["pressure gauge"]

    assert classify_item_status(item, weak_matches) == GapStatus.PARTIAL


def test_scada_or_data_recording_can_be_partial_from_reporting_terms():
    from review.gap_analysis import analyze_checklist_item
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("testing_monitoring")
    item = get_checklist_item(checklist, "scada_or_data_recording")

    text = (
        "The permittee will electronically submit monitoring results. "
        "Daily values and graphs of injection pressure and flow rate will be included "
        "in records submitted to the Director."
    )

    finding = analyze_checklist_item(text, item)

    assert finding.status.value in {"evidence_found", "present"}
    assert "monitoring results" in finding.matched_terms
    assert "daily values" in finding.matched_terms

def test_supporting_excerpts_prefer_item_specific_anchor_terms():
    from review.gap_analysis import find_supporting_excerpts
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("testing_monitoring")
    item = get_checklist_item(checklist, "injection_pressure_monitoring")

    text = (
        "Continuous recording of passive seismic data is processed monthly. "
        "Wellhead pressure and injection pressure will be monitored during operations."
    )

    excerpts = find_supporting_excerpts(
        text=text,
        matched_terms=["continuous recording", "wellhead pressure", "injection pressure"],
        item=item,
        max_excerpts=1,
    )

    assert len(excerpts) == 1
    assert "Wellhead pressure" in excerpts[0]
    assert "passive seismic" not in excerpts[0]

def test_evidence_groups_can_mark_item_present_with_group_coverage():
    from review.gap_analysis import GapStatus, analyze_checklist_item
    from review.types import ReviewChecklistItem, ReviewRequirementLevel, ReviewSeverity

    item = ReviewChecklistItem(
        item_id="injection_pressure_monitoring",
        label="Injection pressure monitoring",
        description="Document should describe pressure monitoring equipment and frequency.",
        requirement_level=ReviewRequirementLevel.REQUIRED,
        severity=ReviewSeverity.CRITICAL,
        expected_evidence_terms=[
            "injection pressure",
            "pressure transducer",
            "continuous",
            "SCADA",
        ],
        evidence_groups={
            "parameter": ["injection pressure", "wellhead pressure"],
            "equipment": ["pressure transducer", "pressure gauge"],
            "frequency": ["continuous", "hourly"],
            "recording": ["SCADA", "data logger"],
        },
        recommended_fix="Describe pressure monitoring equipment, frequency, and data recording.",
    )

    document_text = (
        "The facility will monitor injection pressure using a pressure transducer. "
        "Measurements will be recorded continuously in SCADA."
    )

    finding = analyze_checklist_item(document_text, item)

    assert finding.status == GapStatus.PRESENT
    assert finding.matched_evidence_group_names == [
        "equipment",
        "frequency",
        "parameter",
        "recording",
    ]
    assert finding.matched_evidence_groups["parameter"] == ["injection pressure"]
    assert finding.matched_evidence_groups["equipment"] == ["pressure transducer"]
    assert "matched evidence groups" in finding.finding


def test_evidence_groups_keep_partial_when_only_some_groups_match():
    from review.gap_analysis import GapStatus, analyze_checklist_item
    from review.types import ReviewChecklistItem, ReviewRequirementLevel, ReviewSeverity

    item = ReviewChecklistItem(
        item_id="annular_pressure_monitoring",
        label="Annular pressure monitoring",
        description="Document should describe annular pressure monitoring.",
        requirement_level=ReviewRequirementLevel.REQUIRED,
        severity=ReviewSeverity.CRITICAL,
        expected_evidence_terms=[
            "annular pressure",
            "annulus pressure",
            "continuous",
            "SCADA",
        ],
        evidence_groups={
            "parameter": ["annular pressure", "annulus pressure"],
            "frequency": ["continuous", "hourly"],
            "recording": ["SCADA", "data logger"],
        },
        recommended_fix="Describe annular pressure monitoring frequency and recording method.",
    )

    document_text = "The plan includes annular pressure monitoring."

    finding = analyze_checklist_item(document_text, item)

    assert finding.status == GapStatus.PARTIAL
    assert finding.matched_evidence_group_names == ["parameter"]
    assert finding.matched_evidence_groups["parameter"] == ["annular pressure"]


def test_checklist_item_to_dict_includes_evidence_groups():
    from review.types import ReviewChecklistItem, ReviewRequirementLevel, ReviewSeverity

    item = ReviewChecklistItem(
        item_id="scada_or_data_recording",
        label="SCADA or data recording",
        description="Document should describe electronic monitoring data recording.",
        requirement_level=ReviewRequirementLevel.REQUIRED,
        severity=ReviewSeverity.MODERATE,
        expected_evidence_terms=["SCADA", "data logger"],
        evidence_groups={
            "system": ["SCADA", "data logger"],
            "output": ["daily values", "records"],
        },
    )

    data = item.to_dict()

    assert data["evidence_groups"] == {
        "system": ["SCADA", "data logger"],
        "output": ["daily values", "records"],
    }