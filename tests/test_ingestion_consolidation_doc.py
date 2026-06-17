from pathlib import Path


def test_ingestion_consolidation_plan_exists_and_documents_scope():
    content = Path("docs/ingestion_consolidation.md").read_text(encoding="utf-8")

    assert "Ingestion Consolidation Plan" in content
    assert "Review Document" in content
    assert "Review Package" in content
    assert "rag/chunker.py" in content
    assert "rag/types.py" in content
    assert "ingestion/main.py" in content


def test_ingestion_consolidation_plan_preserves_demo_boundary():
    content = Path("docs/ingestion_consolidation.md").read_text(encoding="utf-8")

    assert "do not refactor ingestion yet" in content
    assert "Review Package for the main demo" in content
    assert "Ask Assistant only after a RAG index is built and validated" in content


def test_ingestion_consolidation_plan_defines_future_branches():
    content = Path("docs/ingestion_consolidation.md").read_text(encoding="utf-8")

    assert "feature/define-canonical-chunk-contract" in content
    assert "feature/extract-shared-section-detection" in content
    assert "feature/implement-minimal-rag-chunking" in content
    assert "feature/consolidate-review-and-rag-ingestion" in content