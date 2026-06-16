from review.temp_ingestion import TemporaryReviewChunk, TemporaryReviewDocument
from review.gap_analysis import analyze_checklist_item
from review.types import (
    ReviewChecklistItem,
    ReviewRequirementLevel,
    ReviewSeverity,
)


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

def test_analyze_checklist_item_includes_confidence_for_missing_item():
    item = ReviewChecklistItem(
        item_id="financial_instrument",
        label="Financial instrument",
        description="Document should identify the financial instrument used for financial responsibility.",
        requirement_level=ReviewRequirementLevel.REQUIRED,
        severity=ReviewSeverity.CRITICAL,
        expected_evidence_terms=["letter of credit", "surety bond"],
        recommended_fix="Add the financial instrument type.",
    )

    finding = analyze_checklist_item(
        "This document discusses unrelated project background.",
        item,
    )

    data = finding.to_dict()

    assert data["status"] == "missing"
    assert data["confidence"] == "High"

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
    assert "appears addressed" in finding.finding
    assert "Evidence was found for equipment, frequency, parameter, and recording." in finding.finding
    assert "Reviewer should confirm" in finding.finding
    assert "matched evidence groups" not in finding.finding


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

def test_find_supporting_excerpts_prioritizes_table_rows():
    from review.gap_analysis import find_supporting_excerpts

    document_text = (
        "The following table summarizes monitoring parameters.\n"
        "Table evidence | page 4 | table 1\n"
        "Table row: Parameter | Frequency | Recording\n"
        "Table row: Injection pressure | Continuous | SCADA\n"
        "The monitoring program is described in the plan."
    )

    excerpts = find_supporting_excerpts(
        document_text,
        matched_terms=["injection pressure", "continuous", "SCADA"],
    )

    assert excerpts
    assert excerpts[0] == "Table row: Injection pressure | Continuous | SCADA"


def test_table_rows_support_evidence_group_matching():
    from review.gap_analysis import GapStatus, analyze_checklist_item
    from review.types import ReviewChecklistItem, ReviewRequirementLevel, ReviewSeverity

    item = ReviewChecklistItem(
        item_id="injection_pressure_monitoring",
        label="Injection pressure monitoring",
        description="Document should describe pressure monitoring.",
        requirement_level=ReviewRequirementLevel.REQUIRED,
        severity=ReviewSeverity.CRITICAL,
        expected_evidence_terms=[
            "injection pressure",
            "continuous",
            "SCADA",
        ],
        evidence_groups={
            "parameter": ["injection pressure"],
            "frequency": ["continuous"],
            "recording": ["SCADA"],
        },
    )

    document_text = (
        "Table evidence | page 4 | table 1\n"
        "Table row: Parameter | Frequency | Recording\n"
        "Table row: Injection pressure | Continuous | SCADA"
    )

    finding = analyze_checklist_item(document_text, item)

    assert finding.status == GapStatus.PRESENT
    assert finding.matched_evidence_group_names == [
        "frequency",
        "parameter",
        "recording",
    ]
    assert finding.supporting_excerpts
    assert finding.supporting_excerpts[0] == (
        "Table row: Injection pressure | Continuous | SCADA"
    )

def test_finding_text_for_present_item_is_reviewer_friendly():
    from review.gap_analysis import GapStatus, build_finding_text
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("testing_monitoring")
    item = get_checklist_item(checklist, "injection_pressure_monitoring")

    text = build_finding_text(
        item=item,
        status=GapStatus.PRESENT,
        matched_terms=["injection pressure", "pressure transducer"],
        matched_group_names=["parameter", "equipment", "frequency", "location"],
    )

    assert "Injection pressure monitoring: appears addressed." in text
    assert "Evidence was found for" in text
    assert "Reviewer should confirm" in text
    assert "matched evidence groups" not in text


def test_finding_text_for_partial_item_names_missing_groups():
    from review.gap_analysis import GapStatus, build_finding_text
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("testing_monitoring")
    item = get_checklist_item(checklist, "injection_pressure_monitoring")

    text = build_finding_text(
        item=item,
        status=GapStatus.PARTIAL,
        matched_terms=["injection pressure"],
        matched_group_names=["parameter"],
    )

    assert "evidence found" in text
    assert "Missing or unconfirmed evidence groups" in text
    assert "equipment" in text
    assert "frequency" in text
    assert "location" in text


def test_finding_text_for_missing_item_gives_next_step():
    from review.gap_analysis import GapStatus, build_finding_text
    from review.schema import get_checklist_item, load_default_checklist

    checklist = load_default_checklist("testing_monitoring")
    item = get_checklist_item(checklist, "annular_pressure_monitoring")

    text = build_finding_text(
        item=item,
        status=GapStatus.MISSING,
        matched_terms=[],
        matched_group_names=[],
    )

    assert "not found in the reviewed text" in text
    assert "No checklist evidence terms were found." in text
    assert "request this information" in text


def test_build_summary_includes_next_step():
    from review.gap_analysis import analyze_document_against_checklist
    from review.schema import load_default_checklist

    document = make_document(
        "Testing and Monitoring Plan. "
        "This section only discusses administrative contacts."
    )

    checklist = load_default_checklist("testing_monitoring")
    report = analyze_document_against_checklist(document, checklist)

    assert "Next step:" in report.summary
    assert "Review missing items first" in report.summary

def test_gap_analysis_includes_page_aware_evidence_locations():
    from review.gap_analysis import analyze_document_against_checklist
    from review.schema import load_default_checklist
    from review.temp_ingestion import TemporaryReviewChunk, TemporaryReviewDocument

    document = TemporaryReviewDocument(
        original_filename="ADM_PISC_and_Site_Closure_Plan.pdf",
        file_extension=".pdf",
        chunks=[
            TemporaryReviewChunk(
                text="General background with no relevant evidence.",
                metadata={
                    "page": 1,
                    "chunk_index": 0,
                    "content_type": "text",
                },
            ),
            TemporaryReviewChunk(
                text=(
                    "The post-injection site care plan proposes a PISC duration "
                    "of 50 years and includes a non-endangerment demonstration."
                ),
                metadata={
                    "page": 12,
                    "chunk_index": 1,
                    "content_type": "text",
                    "section_heading": "PISC Duration",
                },
            ),
        ],
    )

    checklist = load_default_checklist("pisc_site_closure")
    report = analyze_document_against_checklist(document, checklist)
    data = report.to_dict()

    location_findings = [
        finding
        for finding in data["findings"]
        if finding["evidence_locations"]
    ]

    assert location_findings

    first_location = location_findings[0]["evidence_locations"][0]

    assert first_location["file_name"] == "ADM_PISC_and_Site_Closure_Plan.pdf"
    assert first_location["page_number"] == 12
    assert first_location["chunk_index"] == 1
    assert first_location["excerpt"]
    assert first_location["matched_terms"]

def test_analyze_checklist_item_confidence_uses_page_located_evidence():
    item = ReviewChecklistItem(
        item_id="coverage_amount",
        label="Coverage amount",
        description="Document should provide financial responsibility coverage amount evidence.",
        requirement_level=ReviewRequirementLevel.REQUIRED,
        severity=ReviewSeverity.CRITICAL,
        expected_evidence_terms=[
            "financial responsibility",
            "financial assurance",
            "cost estimate",
        ],
        recommended_fix="Confirm the coverage amount.",
    )

    document = TemporaryReviewDocument(
        original_filename="ADM_Cost_Estimates.pdf",
        file_extension=".pdf",
        chunks=[
            TemporaryReviewChunk(
                text=(
                    "The financial responsibility section provides financial assurance "
                    "and a cost estimate for closure."
                ),
                metadata={
                    "page": 4,
                    "chunk_index": 1,
                    "content_type": "text",
                },
            )
        ],
    )

    finding = analyze_checklist_item(
        document,
        "The financial responsibility section provides financial assurance and a cost estimate for closure.",
        item,
    )

    data = finding.to_dict()

    assert data["status"] == "present"
    assert data["confidence"] == "High"
    assert data["evidence_locations"][0]["page_number"] == 4