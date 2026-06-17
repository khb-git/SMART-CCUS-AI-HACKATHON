from demo_samples.maip_demo_package import build_maip_demo_package_response
from review.llm_narrative import (
    LLM_BOUNDARY_NOTICE,
    LlmNarrativeInput,
    build_llm_narrative_prompt,
    build_review_narrative,
)


def test_llm_prompt_preserves_backend_first_boundary():
    package_response = build_maip_demo_package_response()
    report = package_response["report"]

    narrative_input = LlmNarrativeInput(
        package_name=package_response["package_name"],
        overall_status=report["overall_status"],
        summary=report["summary"],
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