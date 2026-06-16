from pathlib import Path


def test_system_assessment_document_exists_and_tracks_next_steps():
    document_path = Path("docs/system_assessment.md")

    assert document_path.exists()

    content = document_path.read_text(encoding="utf-8")

    assert "Backend decides." in content
    assert "Reviewer confirms." in content
    assert "LLM explains." in content
    assert "feature/add-item-level-regulatory-citations" in content
    assert "feature/add-llm-review-narrative-layer" in content
    assert "Regulatory citations" in content
    assert "Reviewer confirmations" in content