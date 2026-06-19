from pathlib import Path


def test_final_demo_release_checklist_documents_judge_runbook():
    checklist = Path("docs/final_demo_release_checklist.md").read_text(
        encoding="utf-8"
    )

    assert "Final Demo Release Checklist and Judge Runbook" in checklist
    assert "Backend decides." in checklist
    assert "Retriever finds." in checklist
    assert "Reviewer confirms." in checklist
    assert "LLM explains." in checklist
    assert "python -m pytest tests/" in checklist
    assert "python -m uvicorn api.main:app --reload" in checklist
    assert "python -m streamlit run ui/app.py" in checklist
    assert "http://127.0.0.1:8000/demo/maip-package" in checklist
    assert "http://127.0.0.1:8000/demo/maip-package/report" in checklist
    assert "http://127.0.0.1:8000/demo/maip-package/final-packet" in checklist


def test_final_demo_release_checklist_documents_reviewer_boundaries():
    checklist = Path("docs/final_demo_release_checklist.md").read_text(
        encoding="utf-8"
    )

    assert "not a final regulatory determination" in checklist
    assert "qualified reviewer" in checklist
    assert "OCR is visible text only" in checklist
    assert "does not infer hidden redacted content" in checklist.lower()
    assert "Evidence found does not automatically mean" in checklist


def test_readme_links_final_demo_release_checklist():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "docs/final_demo_release_checklist.md" in readme