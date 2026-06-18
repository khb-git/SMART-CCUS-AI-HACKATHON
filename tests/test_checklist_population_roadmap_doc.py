from pathlib import Path


def test_checklist_population_roadmap_exists():
    path = Path("docs/checklist_population_roadmap.md")

    assert path.exists()

    text = path.read_text(encoding="utf-8")

    assert "Checklist Population Roadmap" in text
    assert "Backend decides." in text
    assert "Retriever finds." in text
    assert "Reviewer confirms." in text
    assert "LLM explains." in text


def test_checklist_population_roadmap_captures_core_workflow():
    text = Path("docs/checklist_population_roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "GSDT Module/Folder" in text
    assert "File Name" in text
    assert "Page Number" in text
    assert "Reviewer notes" in text
    assert "populated Class VI completeness checklist" in text
    assert "temporary package retrieval" in text.lower()