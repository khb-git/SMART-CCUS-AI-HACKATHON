from review.maip_validation import (
    MaipEvidenceValue,
    MaipValidationInput,
    MaipValidationSeverity,
    MaipValidationStatus,
    validate_maip_chain,
)


def value(concept: str, numeric_value: float) -> MaipEvidenceValue:
    return MaipEvidenceValue(
        concept=concept,
        value=numeric_value,
        unit="psi",
        source_file="test.pdf",
        page_number=4,
        excerpt=f"{concept} = {numeric_value} psi",
        confidence="High",
    )


def complete_valid_input() -> MaipValidationInput:
    return MaipValidationInput(
        proposed_maip=value("proposed_maip", 1800.0),
        fracture_pressure=value("fracture_pressure", 2200.0),
        aor_model_max_pressure=value("aor_model_max_pressure", 2000.0),
        casing_pressure_rating=value("casing_pressure_rating", 3000.0),
        annulus_pressure_limit=value("annulus_pressure_limit", 2500.0),
        operating_pressure_limit=value("operating_pressure_limit", 1900.0),
        annulus_management_evidence=MaipEvidenceValue(
            concept="annulus_management_evidence",
            excerpt="Annulus pressure will be monitored continuously.",
            confidence="Medium",
        ),
        operating_margin_evidence=MaipEvidenceValue(
            concept="operating_margin_evidence",
            excerpt="The operating pressure remains below limiting pressure conditions.",
            confidence="Medium",
        ),
    )


def finding_by_id(report, finding_id: str):
    return next(
        finding
        for finding in report.findings
        if finding.finding_id == finding_id
    )


def test_maip_validation_passes_for_consistent_structured_values():
    report = validate_maip_chain(complete_valid_input())

    assert report.overall_status == MaipValidationStatus.PASS
    assert "MAIP validation complete" in report.summary
    assert all(finding.status == MaipValidationStatus.PASS for finding in report.findings)


def test_maip_validation_flags_missing_maip_evidence():
    validation_input = complete_valid_input()
    validation_input.proposed_maip = None

    report = validate_maip_chain(validation_input)
    finding = finding_by_id(report, "maip_evidence_present")

    assert report.overall_status == MaipValidationStatus.MISSING_EVIDENCE
    assert finding.status == MaipValidationStatus.MISSING_EVIDENCE
    assert finding.severity == MaipValidationSeverity.HIGH
    assert "does not provide a clear proposed Maximum Allowable Injection Pressure" in finding.message


def test_maip_validation_flags_missing_fracture_pressure_evidence():
    validation_input = complete_valid_input()
    validation_input.fracture_pressure = None
    validation_input.fracture_gradient = None

    report = validate_maip_chain(validation_input)
    finding = finding_by_id(report, "fracture_pressure_evidence_present")

    assert report.overall_status == MaipValidationStatus.MISSING_EVIDENCE
    assert finding.status == MaipValidationStatus.MISSING_EVIDENCE
    assert finding.severity == MaipValidationSeverity.HIGH
    assert "fracture pressure or fracture gradient evidence" in finding.message


def test_maip_validation_fails_when_maip_exceeds_90_percent_fracture_pressure():
    validation_input = complete_valid_input()
    validation_input.proposed_maip = value("proposed_maip", 2050.0)
    validation_input.fracture_pressure = value("fracture_pressure", 2200.0)

    report = validate_maip_chain(validation_input)
    finding = finding_by_id(report, "maip_below_90_percent_fracture_pressure")

    assert report.overall_status == MaipValidationStatus.FAIL
    assert finding.status == MaipValidationStatus.FAIL
    assert finding.severity == MaipValidationSeverity.CRITICAL
    assert "exceeds 90% of the cited fracture pressure" in finding.message


def test_maip_validation_warns_for_narrow_fracture_pressure_margin():
    validation_input = complete_valid_input()
    validation_input.proposed_maip = value("proposed_maip", 1900.0)
    validation_input.fracture_pressure = value("fracture_pressure", 2200.0)

    report = validate_maip_chain(validation_input)
    finding = finding_by_id(report, "maip_below_90_percent_fracture_pressure")

    assert report.overall_status == MaipValidationStatus.WARNING
    assert finding.status == MaipValidationStatus.WARNING
    assert finding.severity == MaipValidationSeverity.MODERATE
    assert "narrow operating margin" in finding.message


def test_maip_validation_fails_when_maip_exceeds_aor_model_pressure():
    validation_input = complete_valid_input()
    validation_input.proposed_maip = value("proposed_maip", 2100.0)
    validation_input.fracture_pressure = value("fracture_pressure", 2500.0)
    validation_input.aor_model_max_pressure = value("aor_model_max_pressure", 2000.0)

    report = validate_maip_chain(validation_input)
    finding = finding_by_id(report, "maip_within_aor_model_pressure")

    assert report.overall_status == MaipValidationStatus.FAIL
    assert finding.status == MaipValidationStatus.FAIL
    assert finding.severity == MaipValidationSeverity.HIGH
    assert "exceeds the pressure constraint represented in the AoR model" in finding.message


def test_maip_validation_fails_when_maip_not_below_casing_rating():
    validation_input = complete_valid_input()
    validation_input.proposed_maip = value("proposed_maip", 2200.0)
    validation_input.fracture_pressure = value("fracture_pressure", 2600.0)
    validation_input.aor_model_max_pressure = value("aor_model_max_pressure", 2400.0)
    validation_input.casing_pressure_rating = value("casing_pressure_rating", 2200.0)

    report = validate_maip_chain(validation_input)
    finding = finding_by_id(report, "maip_below_casing_pressure_rating")

    assert report.overall_status == MaipValidationStatus.FAIL
    assert finding.status == MaipValidationStatus.FAIL
    assert finding.severity == MaipValidationSeverity.CRITICAL
    assert "not below the cited casing pressure rating" in finding.message


def test_maip_validation_warns_when_annulus_management_evidence_missing():
    validation_input = complete_valid_input()
    validation_input.annulus_management_evidence = None
    validation_input.annulus_pressure_limit = None

    report = validate_maip_chain(validation_input)
    finding = finding_by_id(report, "annulus_management_evidence_present")

    assert report.overall_status == MaipValidationStatus.WARNING
    assert finding.status == MaipValidationStatus.WARNING
    assert finding.severity == MaipValidationSeverity.MODERATE
    assert "does not provide clear annulus pressure management evidence" in finding.message


def test_maip_validation_warns_when_operating_margin_evidence_missing():
    validation_input = complete_valid_input()
    validation_input.operating_margin_evidence = None
    validation_input.operating_pressure_limit = None

    report = validate_maip_chain(validation_input)
    finding = finding_by_id(report, "operating_margin_evidence_present")

    assert report.overall_status == MaipValidationStatus.WARNING
    assert finding.status == MaipValidationStatus.WARNING
    assert finding.severity == MaipValidationSeverity.MODERATE
    assert "does not clearly document the operating margin" in finding.message


def test_maip_validation_report_is_json_serializable():
    report = validate_maip_chain(complete_valid_input())
    report_dict = report.to_dict()

    assert report_dict["overall_status"] == "pass"
    assert "summary" in report_dict
    assert isinstance(report_dict["findings"], list)
    assert report_dict["findings"][0]["supporting_values"][0]["source_file"] == "test.pdf"