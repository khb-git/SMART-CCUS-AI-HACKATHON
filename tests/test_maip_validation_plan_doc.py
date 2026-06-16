from pathlib import Path


def test_maip_validation_plan_exists_and_names_core_chain():
    content = Path("docs/maip_validation_plan.md").read_text(encoding="utf-8")

    assert "MAIP Cross-Reference Validation Plan" in content
    assert "fracture pressure" in content
    assert "MAIP at 90% fracture pressure" in content
    assert "AoR model pressure constraint" in content
    assert "casing adequacy" in content
    assert "annulus management" in content
    assert "operating margin" in content


def test_maip_validation_plan_preserves_backend_first_boundary():
    content = Path("docs/maip_validation_plan.md").read_text(encoding="utf-8")

    assert "Backend decides." in content
    assert "Reviewer confirms." in content
    assert "LLM explains." in content
    assert "The validator should be deterministic" in content
    assert "use an LLM to decide MAIP validity" in content


def test_maip_validation_plan_defines_future_branches():
    content = Path("docs/maip_validation_plan.md").read_text(encoding="utf-8")

    assert "feature/add-maip-validation-core" in content
    assert "feature/add-maip-evidence-extraction" in content
    assert "feature/add-maip-package-review-integration" in content
    assert "feature/add-maip-export-support" in content
    assert "feature/add-maip-ui-panel" in content