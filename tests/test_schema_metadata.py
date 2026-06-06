import json


def test_infer_plan_type_from_filename():
    import ingestion.main as ingestion_main

    assert (
        ingestion_main.infer_plan_type("ADM_Testing_and_Monitoring_Plan.pdf")
        == "testing_monitoring"
    )

    assert (
        ingestion_main.infer_plan_type("HGCS_AoR_and_Corrective_Action_Plan.pdf")
        == "aor_corrective_action"
    )

    assert (
        ingestion_main.infer_plan_type("Wabash_Well_Construction_Plan.pdf")
        == "well_construction"
    )

    assert (
        ingestion_main.infer_plan_type("One_Earth_Project_Narrative.pdf")
        == "project_narrative"
    )


def test_infer_plan_type_from_manifest_summary():
    import ingestion.main as ingestion_main

    metadata = {
        "summary": "Emergency and Remedial Response Plan for Class VI permit",
        "url": "https://example.com/file.pdf",
        "source_page": "https://example.com/docket",
    }

    assert (
        ingestion_main.infer_plan_type("file.pdf", metadata)
        == "emergency_remedial_response"
    )


def test_build_review_metadata_returns_schema_section():
    import ingestion.main as ingestion_main

    metadata = ingestion_main.build_review_metadata(
        "ADM_Pre-Operational_Testing.pdf",
        {},
    )

    assert metadata["plan_type"] == "pre_operational_testing"
    assert metadata["schema_section_id"] == "6"
    assert metadata["schema_section_title"] == "Pre-Operational Testing Plan"


def test_written_chunks_include_schema_metadata(tmp_path):
    import ingestion.main as ingestion_main

    file_path = tmp_path / "ADM_Testing_and_Monitoring_Plan.pdf"
    file_path.write_bytes(b"%PDF fake")

    output_dir = tmp_path / "chunked"

    chunk = ingestion_main.IngestionDocument(
        page_content="Monitoring well frequency table.",
        metadata={
            "page": 0,
            "content_type": "text",
        },
    )

    count = ingestion_main.write_chunks_for_document(
        file_path=file_path,
        chunks=[chunk],
        output_root=output_dir,
        metadata={
            "url": "https://example.com/adm_tm_plan.pdf",
            "source_page": "https://example.com/docket",
            "summary": "ADM Testing and Monitoring Plan",
        },
    )

    assert count == 1

    document_dir = output_dir / "ADM_Testing_and_Monitoring_Plan"

    document_attr = json.loads(
        (document_dir / "attribute.json").read_text(encoding="utf-8")
    )

    assert document_attr["plan_type"] == "testing_monitoring"
    assert document_attr["schema_section_id"] == "8"
    assert document_attr["schema_section_title"] == "Testing and Monitoring Plan"

    chunk_attr = json.loads(
        (document_dir / "0" / "attribute.json").read_text(encoding="utf-8")
    )

    assert chunk_attr["plan_type"] == "testing_monitoring"
    assert chunk_attr["schema_section_id"] == "8"
    assert chunk_attr["schema_section_title"] == "Testing and Monitoring Plan"