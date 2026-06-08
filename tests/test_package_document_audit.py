from pathlib import Path


MARQUIS_FILES = [
    "Marquis_Alternative_PISC_Timeframe__4b09b5518eb0.pdf",
    "Marquis_AoR_and_Corrective_Action_Plan__372a3b7147c5.pdf",
    "Marquis_Cost_Estimates__d2ecd510f852.pdf",
    "Marquis_ERRP_0__1080df019d02.pdf",
    "Marquis_Injection_Well_Plugging_Plan__064bb3574fb3.pdf",
    "Marquis_Narrative__c0be5d66081e.pdf",
    "Marquis_PISC_and_Site_Closure_Plan__36aa081feef7.pdf",
    "Marquis_Pre-Operational_Testing__b7ec72e5ea1e.pdf",
    "Marquis_Testing_and_Monitoring_Plan__745f3e668e45.pdf",
    "Marquis_Well_Construction_Plan__5ae2514e6639.pdf",
]


def test_normalize_filename_removes_scraped_hash_suffix():
    from review.package_document_audit import normalize_filename

    assert normalize_filename(
        "Marquis_Testing_and_Monitoring_Plan__745f3e668e45.pdf"
    ) == "marquis testing and monitoring plan"


def test_audit_package_document_name_maps_main_document_type():
    from review.package_document_audit import audit_package_document_name

    result = audit_package_document_name(
        "Marquis_Testing_and_Monitoring_Plan__745f3e668e45.pdf"
    )

    assert result.document_type == "testing_monitoring"
    assert result.document_role == "main"
    assert result.matched_aliases
    assert result.reason


def test_audit_package_document_name_maps_supporting_document_type():
    from review.package_document_audit import audit_package_document_name

    result = audit_package_document_name(
        "Marquis_Alternative_PISC_Timeframe__4b09b5518eb0.pdf"
    )

    assert result.document_type == "supporting_pisc_alternative_timeframe"
    assert result.document_role == "supporting"
    assert "alternative pisc timeframe" in result.matched_aliases


def test_audit_marquis_package_documents_matches_expected_types():
    from review.package_document_audit import audit_package_documents

    expected_main_document_types = [
        "aor_corrective_action",
        "emergency_remedial_response",
        "financial_responsibility",
        "injection_well_plugging",
        "pisc_site_closure",
        "pre_operational_testing",
        "project_narrative",
        "testing_monitoring",
        "well_construction",
    ]

    report = audit_package_documents(
        MARQUIS_FILES,
        package_name="marquis_putnam_county",
        expected_main_document_types=expected_main_document_types,
    )

    assert report.package_name == "marquis_putnam_county"
    assert report.detected_main_document_types == sorted(expected_main_document_types)
    assert report.detected_supporting_document_types == [
        "supporting_pisc_alternative_timeframe"
    ]
    assert report.unknown_documents == []
    assert report.missing_expected_main_document_types == []

    data = report.to_dict()

    assert data["package_name"] == "marquis_putnam_county"
    assert data["audited_documents"]
    assert data["detected_main_document_types"] == sorted(expected_main_document_types)


def test_audit_marquis_package_shows_site_operating_and_geology_missing_when_expected():
    from review.package_document_audit import audit_package_documents

    expected_main_document_types = [
        "aor_corrective_action",
        "emergency_remedial_response",
        "financial_responsibility",
        "injection_well_plugging",
        "pisc_site_closure",
        "pre_operational_testing",
        "project_narrative",
        "site_geologic_characterization",
        "site_operating",
        "testing_monitoring",
        "well_construction",
    ]

    report = audit_package_documents(
        MARQUIS_FILES,
        package_name="marquis_putnam_county",
        expected_main_document_types=expected_main_document_types,
    )

    assert report.missing_expected_main_document_types == [
        "site_geologic_characterization",
        "site_operating",
    ]


def test_audit_unknown_document_name():
    from review.package_document_audit import audit_package_document_name

    result = audit_package_document_name("Marquis_Random_Attachment.pdf")

    assert result.document_type == "unknown"
    assert result.document_role == "unknown"
    assert result.matched_aliases == []


def test_find_package_files(tmp_path):
    from review.package_document_audit import find_package_files

    raw_docs = tmp_path / "data" / "raw_docs"
    raw_docs.mkdir(parents=True)

    marquis_file = raw_docs / "Marquis_Testing_and_Monitoring_Plan.pdf"
    adm_file = raw_docs / "ADM_Testing_and_Monitoring_Plan.pdf"
    notes_file = raw_docs / "Marquis_notes.txt"

    marquis_file.write_text("fake pdf", encoding="utf-8")
    adm_file.write_text("fake pdf", encoding="utf-8")
    notes_file.write_text("ignore txt", encoding="utf-8")

    matches = find_package_files(
        raw_docs,
        package_terms=["Marquis"],
    )

    assert matches == [marquis_file]