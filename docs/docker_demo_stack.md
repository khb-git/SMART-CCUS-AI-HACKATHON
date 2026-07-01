# Docker Demo Stack

This project includes a local Docker stack for running the SMART CCUS Class VI
Review Assistant with consistent dependencies.

The stack is useful for demos, reproducibility, and future on-premise deployment
work.

## What the stack runs

```text
FastAPI backend
Streamlit UI
Ollama local LLM runtime, optional
Persistent Chroma data volume
```

The strongest demo workflow is still:

```text
Review Package
```

The deterministic MAIP demo endpoints also work inside Docker.

## Architecture

```text
Browser
→ Streamlit UI
→ FastAPI backend
→ local review engine / Chroma data / optional Ollama
→ reviewer-facing outputs
```

Core project boundary:

```text
Backend decides.
Retriever finds.
Reviewer confirms.
LLM explains.
```

## Build the stack

From the repository root:

```powershell
docker compose build
```

The build installs Python dependencies, installs Tesseract OCR, and pre-downloads
the local embedding model used by the retrieval layer.

## Start the stack

```powershell
docker compose up
```

Open the UI:

```text
http://localhost:8501
```

Open the backend docs:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/health
```

## Demo endpoints

With the backend running, open:

```text
http://localhost:8000/demo/maip-package
http://localhost:8000/demo/maip-package/report
http://localhost:8000/demo/maip-package/final-packet
```

These endpoints use deterministic in-memory demo data. They do not require
uploaded files, a populated RAG index, Ollama, or an external LLM service.

## OCR support

The Docker image installs Tesseract OCR.

OCR-derived evidence is visible text only. The system does not inspect, recover,
or infer hidden redacted content.

## Optional Ollama model preload

The Review Package workflow and deterministic MAIP demo do not require Ollama.

For optional future LLM narrative use, preload a local model while connected:

```powershell
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.1
```

Then restart the stack:

```powershell
docker compose up
```

## Air-gap note

This Docker setup is structured toward on-premise and air-gapped deployment, but
a full offline deployment requires extra packaging steps:

```text
Build images on a connected machine
Preload required model caches and Ollama models
Export Docker images
Transfer images and model volumes to the isolated host
Load images on the isolated host
Run docker compose up without internet
```

Do not claim full air-gap readiness unless the images and model volumes have
been tested on a machine without network access.

## Useful commands

Build:

```powershell
docker compose build
```

Start:

```powershell
docker compose up
```

Start in the background:

```powershell
docker compose up -d
```

Stop:

```powershell
docker compose down
```

Stop and remove volumes:

```powershell
docker compose down -v
```

View logs:

```powershell
docker compose logs -f
```

View backend logs:

```powershell
docker compose logs -f backend
```

View UI logs:

```powershell
docker compose logs -f ui
```

## Judge demo path

1. Run `docker compose up`.
2. Open `http://localhost:8501`.
3. Use the Review Package tab.
4. Upload Class VI-style review documents.
5. Show detected document types.
6. Show package review metrics.
7. Show reviewer action items.
8. Show completeness checklist rows.
9. Show citations and evidence locations.
10. Export the final review packet.

Backup demo:

```text
http://localhost:8000/demo/maip-package/final-packet
```