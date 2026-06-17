from pathlib import Path


def test_demo_readiness_checklist_documents_core_demo_flow():
    content = Path("docs/demo_readiness_checklist.md").read_text(encoding="utf-8")

    assert "Backend decides." in content
    assert "Reviewer confirms." in content
    assert "LLM explains." in content
    assert "Load deterministic MAIP demo package" in content
    assert "Generate reviewer narrative" in content
    assert "MAIP Cross-Reference Validation" in content
    assert "reviewer_narrative.md" not in content


def test_demo_readiness_checklist_documents_runtime_commands():
    content = Path("docs/demo_readiness_checklist.md").read_text(encoding="utf-8")

    assert "python -m uvicorn api.main:app --reload" in content
    assert "python -m streamlit run ui/app.py" in content
    assert "python -m pytest tests/" in content
    assert "http://127.0.0.1:8000/docs" in content
    assert "http://localhost:8501" in content