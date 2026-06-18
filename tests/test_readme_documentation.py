from pathlib import Path


def test_readme_documents_current_demo_and_ocr_workflow():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "Backend decides." in readme
    assert "Retriever finds." in readme
    assert "Reviewer confirms." in readme
    assert "LLM explains." in readme
    assert "Review Package" in readme
    assert "tesseract --version" in readme
    assert "image_ocr" in readme
    assert "redacted_image_ocr" in readme
    assert "docs/ocr_validation_workflow.md" in readme
    assert "docs/real_document_validation_workflow.md" in readme
    assert "docs/validation_to_regression_workflow.md" in readme


def test_readme_documents_reviewer_boundaries():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "not a final regulatory determination" in readme
    assert "qualified reviewer" in readme
    assert "does not inspect, recover, or infer hidden content" in readme
    assert "docs/reviewer_disclaimers_and_limitations.md" in readme