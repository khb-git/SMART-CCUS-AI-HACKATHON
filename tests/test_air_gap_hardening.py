from pathlib import Path


def test_air_gapped_requirements_exclude_cloud_llm_sdks():
    requirements = Path("requirements.txt").read_text(encoding="utf-8")

    assert "langchain-ollama" in requirements
    assert "langchain-openai" not in requirements
    assert "langchain-anthropic" not in requirements


def test_dev_requirements_include_cloud_llm_sdks_with_warning():
    dev_requirements = Path("requirements-dev.txt").read_text(encoding="utf-8")

    assert "Development-only cloud SDKs" in dev_requirements
    assert "air-gapped deployment" in dev_requirements
    assert "langchain-openai>=1.2.1" in dev_requirements
    assert "langchain-anthropic>=1.4.3" in dev_requirements


def test_env_example_disables_anonymized_telemetry():
    env_example = Path(".env.example").read_text(encoding="utf-8")

    assert "ANONYMIZED_TELEMETRY=False" in env_example