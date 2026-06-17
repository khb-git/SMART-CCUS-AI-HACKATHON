from demo_samples.maip_demo_package import build_maip_demo_package_response
from review.llm_narrative import (
    LLM_BOUNDARY_NOTICE,
    LlmNarrativeInput,
    build_llm_narrative_prompt,
    build_review_narrative,
)

DEMO_PACKAGE_METRICS = {
    "total_checklist_rows": 6,
    "missing_rows": 0,
    "required_missing_rows": 0,
    "critical_missing_rows": 0,
    "evidence_found_rows": 4,
    "page_located_percent": "100%",
}


DEMO_PACKAGE_COUNTS = {
    "detected_document_types_count": 5,
    "missing_required_document_types_count": 5,
    "missing_expected_document_types_count": 5,
    "supporting_documents_count": 0,
    "duplicate_document_types_count": 0,
    "unknown_documents_count": 0,
    "detected_document_types": [
        "site_operating",
        "site_geologic_characterization",
        "aor_corrective_action",
        "well_construction",
        "testing_monitoring",
    ],
    "missing_required_document_types": [
        "project_narrative",
        "financial_responsibility",
        "injection_well_plugging",
        "pisc_site_closure",
        "emergency_remedial_response",
    ],
    "missing_expected_document_types": [
        "project_narrative",
        "financial_responsibility",
        "injection_well_plugging",
        "pisc_site_closure",
        "emergency_remedial_response",
    ],
    "supporting_documents": [],
    "duplicate_document_types": [],
    "unknown_documents": [],
}

def test_llm_prompt_preserves_backend_first_boundary():
    package_response = build_maip_demo_package_response()
    report = package_response["report"]

    narrative_input = LlmNarrativeInput(
        package_name=package_response["package_name"],
        overall_status=report["overall_status"],
        summary=report["summary"],
        package_metrics=DEMO_PACKAGE_METRICS,
        package_counts=DEMO_PACKAGE_COUNTS,
        reviewer_action_items=["Confirm cited MAIP evidence."],
        priority_checklist_rows=[],
        maip_validation=report["maip_validation"],
        reviewer_confirmations=[],
    )

    prompt = build_llm_narrative_prompt(narrative_input)

    assert "Backend decides." in prompt
    assert "Reviewer confirms." in prompt
    assert "LLM explains." in prompt
    assert "Do not change statuses" in prompt
    assert "Do not invent evidence" in prompt
    assert "maip_evidence_present" in prompt
    assert "proposed_maip" in prompt


def test_template_review_narrative_uses_deterministic_maip_results():
    package_response = build_maip_demo_package_response()
    report = package_response["report"]

    narrative_input = LlmNarrativeInput(
        package_name=package_response["package_name"],
        overall_status=report["overall_status"],
        summary=report["summary"],
        package_metrics=DEMO_PACKAGE_METRICS,
        package_counts=DEMO_PACKAGE_COUNTS,
        reviewer_action_items=["Confirm cited MAIP evidence."],
        priority_checklist_rows=[],
        maip_validation=report["maip_validation"],
        reviewer_confirmations=[],
    )

    result = build_review_narrative(narrative_input)

    assert result.used_llm is False
    assert result.model_name == "deterministic-template"
    assert LLM_BOUNDARY_NOTICE in result.narrative
    assert "maip_demo_package" in result.narrative
    assert "pass" in result.narrative
    assert "maip_evidence_present" in result.narrative
    assert "proposed_maip" in result.narrative


def test_llm_review_narrative_falls_back_when_llm_fails(monkeypatch):
    package_response = build_maip_demo_package_response()
    report = package_response["report"]

    narrative_input = LlmNarrativeInput(
        package_name=package_response["package_name"],
        overall_status=report["overall_status"],
        summary=report["summary"],
        package_metrics=DEMO_PACKAGE_METRICS,
        package_counts=DEMO_PACKAGE_COUNTS,
        reviewer_action_items=[],
        priority_checklist_rows=[],
        maip_validation=report["maip_validation"],
        reviewer_confirmations=[],
    )

    
    def fake_generate(*args, **kwargs):
        raise RuntimeError("ollama unavailable")

    monkeypatch.setattr(
        "review.llm_narrative.try_generate_ollama_narrative",
        fake_generate,
    )

    result = build_review_narrative(
        narrative_input,
        use_llm=True,
        model_name="fake-model",
    )

    assert result.used_llm is False
    assert result.model_name == "deterministic-template-fallback"
    assert LLM_BOUNDARY_NOTICE in result.narrative

def test_prompt_preserves_exact_marquis_style_counts():
    narrative_input = LlmNarrativeInput(
        package_name="uploaded_package",
        overall_status="needs_revision",
        summary=(
            "Package review complete. Detected document types: 9; "
            "Missing required document types: 0; Missing expected document types: 0; "
            "Duplicate document types: 0; Supporting documents: 1; Unknown documents: 0."
        ),
        package_metrics={
            "total_checklist_rows": 95,
            "present_rows": 51,
            "evidence_found_rows": 32,
            "missing_rows": 12,
            "unclear_rows": 0,
            "required_missing_rows": 7,
            "critical_missing_rows": 6,
            "page_located_percent": "87%",
            "resolved_percent": "87%",
        },
        package_counts={
            "detected_document_types_count": 9,
            "missing_required_document_types_count": 0,
            "missing_expected_document_types_count": 0,
            "supporting_documents_count": 1,
            "duplicate_document_types_count": 0,
            "unknown_documents_count": 0,
            "detected_document_types": [
                "aor_corrective_action",
                "emergency_remedial_response",
                "financial_responsibility",
                "injection_well_plugging",
                "pisc_site_closure",
                "pre_operational_testing",
                "project_narrative",
                "testing_monitoring",
                "well_construction",
            ],
            "missing_required_document_types": [],
            "missing_expected_document_types": [],
            "supporting_documents": ["Marquis_Alternative_PISC_Timeframe.pdf"],
            "duplicate_document_types": [],
            "unknown_documents": [],
        },
        reviewer_action_items=[
            "Resolve 6 critical missing checklist row(s).",
            "Resolve 7 required missing checklist row(s).",
            "Review 32 evidence-found row(s) to confirm whether the cited evidence fully satisfies the checklist item.",
            "Review 24 low-confidence row(s) for weak or unclear evidence support.",
        ],
        priority_checklist_rows=[
            {
                "status": "missing",
                "required_item": "Financial instrument",
                "module_folder": "Financial Responsibility",
                "regulatory_citation": "40 CFR 146.85 - Financial responsibility",
                "file_name": "Marquis_Cost_Estimates.pdf",
                "page_number": "Not found",
                "notes": "Financial instrument: not found in the reviewed text.",
            }
        ],
        maip_validation={
            "overall_status": "missing_evidence",
            "summary": (
                "MAIP validation complete. Pass: 1; Warnings: 1; "
                "Failures: 0; Missing evidence: 5."
            ),
            "findings": [
                {
                    "finding_id": "maip_evidence_present",
                    "status": "missing_evidence",
                    "severity": "high",
                    "message": "The package does not provide a clear proposed MAIP.",
                    "supporting_values": [],
                }
            ],
        },
        reviewer_confirmations=[],
    )

    prompt = build_llm_narrative_prompt(narrative_input)
    result = build_review_narrative(narrative_input)

    assert "unknown_documents_count: 0" in prompt
    assert "supporting_documents_count: 1" in prompt
    assert "missing_rows: 12" in prompt
    assert "required_missing_rows: 7" in prompt
    assert "Do not infer new counts." in prompt
    assert "Do not mention unknown documents unless unknown_documents_count is greater than 0." in prompt

    assert "missing rows=12" in result.narrative
    assert "required missing rows=7" in result.narrative
    assert "supporting documents=1" in result.narrative
    assert "unknown documents=0" in result.narrative