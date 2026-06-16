from review.maip_validation import MaipValidationStatus
from review.package_review import (
    PackageDocumentReview,
    ReviewPackageReport,
    build_package_maip_validation_report,
)


def test_package_maip_validation_report_is_conservative_without_extraction():
    report = build_package_maip_validation_report([])

    assert report.overall_status == MaipValidationStatus.MISSING_EVIDENCE
    assert "MAIP validation complete" in report.summary

    finding_ids = {
        finding.finding_id
        for finding in report.findings
    }

    assert "maip_evidence_present" in finding_ids
    assert "fracture_pressure_evidence_present" in finding_ids
    assert "maip_below_90_percent_fracture_pressure" in finding_ids


def test_review_package_report_serializes_maip_validation():
    maip_validation = build_package_maip_validation_report([])

    package_report = ReviewPackageReport(
        package_name="test_package",
        overall_status="needs_review",
        summary="Package review complete.",
        expected_plan_types=[],
        required_plan_types=[],
        detected_plan_types=[],
        missing_required_plan_types=[],
        missing_expected_plan_types=[],
        duplicate_plan_types=[],
        unknown_documents=[],
        supporting_documents=[],
        coverage_evidence=[],
        document_reviews=[],
        maip_validation=maip_validation,
    )

    report_dict = package_report.to_dict()

    assert "maip_validation" in report_dict
    assert report_dict["maip_validation"]["overall_status"] == "missing_evidence"
    assert isinstance(report_dict["maip_validation"]["findings"], list)


def test_review_package_report_allows_missing_maip_validation_for_compatibility():
    package_report = ReviewPackageReport(
        package_name="test_package",
        overall_status="needs_review",
        summary="Package review complete.",
        expected_plan_types=[],
        required_plan_types=[],
        detected_plan_types=[],
        missing_required_plan_types=[],
        missing_expected_plan_types=[],
        duplicate_plan_types=[],
        unknown_documents=[],
        supporting_documents=[],
        coverage_evidence=[],
        document_reviews=[
            PackageDocumentReview(
                document_name="unknown.pdf",
                document_type="unknown",
                classification_confidence="Low",
                classification={},
            )
        ],
        maip_validation=None,
    )

    report_dict = package_report.to_dict()

    assert "maip_validation" in report_dict
    assert report_dict["maip_validation"] is None