from pathlib import Path


def test_dockerfile_installs_tesseract_and_runs_backend():
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "FROM python:3.11-slim" in dockerfile
    assert "tesseract-ocr" in dockerfile
    assert "pip install" in dockerfile
    assert "BAAI/bge-base-en-v1.5" in dockerfile
    assert "uvicorn" in dockerfile
    assert "api.main:app" in dockerfile
    assert "EXPOSE 8000 8501" in dockerfile


def test_docker_compose_defines_backend_ui_and_ollama():
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")

    assert "backend:" in compose
    assert "ui:" in compose
    assert "ollama:" in compose
    assert "SMART_CCUS_API_URL: http://backend:8000" in compose
    assert '"8000:8000"' in compose
    assert '"8501:8501"' in compose
    assert "chroma_data:" in compose
    assert "ollama_models:" in compose


def test_dockerignore_excludes_local_runtime_artifacts():
    dockerignore = Path(".dockerignore").read_text(encoding="utf-8")

    assert ".venv" in dockerignore
    assert "__pycache__" in dockerignore
    assert "data/raw_docs" in dockerignore
    assert "data/chunked" in dockerignore
    assert "chroma_data" in dockerignore
    assert ".env" in dockerignore


def test_docker_demo_docs_include_run_commands_and_boundaries():
    docs = Path("docs/docker_demo_stack.md").read_text(encoding="utf-8")

    assert "docker compose build" in docs
    assert "docker compose up" in docs
    assert "http://localhost:8501" in docs
    assert "http://localhost:8000/health" in docs
    assert "http://localhost:8000/demo/maip-package/final-packet" in docs
    assert "OCR-derived evidence is visible text only" in docs
    assert "Do not claim full air-gap readiness" in docs