from pathlib import Path


def test_readme_sets_demo_expectations():
    content = Path("README.md").read_text(encoding="utf-8")

    assert "Backend decides." in content
    assert "Reviewer confirms." in content
    assert "LLM explains." in content
    assert "Review Package" in content
    assert "recommended demo path" in content
    assert "Ask Assistant requires a populated RAG index" in content


def test_readme_documents_reviewer_exports():
    content = Path("README.md").read_text(encoding="utf-8")

    assert "Final Review Packet" in content
    assert "Deficiency CSV" in content
    assert "Reviewer State JSON" in content
    assert "Reviewer confirmations" in content
    assert "Reviewer notes" in content
    assert "regulatory citations" in content


def test_readme_includes_run_commands():
    content = Path("README.md").read_text(encoding="utf-8")

    assert "python -m uvicorn api.main:app --reload" in content
    assert "python -m streamlit run ui/app.py" in content
    assert "python -m pytest tests/" in content