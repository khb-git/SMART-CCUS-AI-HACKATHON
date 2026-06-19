# NittCarb AI — shared application image for FastAPI backend and Streamlit UI.
#
# One image serves both Python services. docker-compose selects which process
# runs through the command field.
#
# Chroma currently runs through the Python application using the local
# ./chroma_data path, persisted by a Docker named volume.

FROM python:3.11-slim

ENV HF_HOME=/opt/hf-cache \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HUB_DISABLE_TELEMETRY=1 \
    ANONYMIZED_TELEMETRY=False

WORKDIR /app

# System dependencies:
# - tesseract-ocr is required by pytesseract.
# - libgomp1 is commonly needed by ML/scientific Python wheels.
# - curl is useful for manual container debugging.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the local embedding model so the running container can use the
# baked cache instead of pulling the model at runtime.
#
# Model name matches rag/embeddings.py:
# DEFAULT_MODEL = "BAAI/bge-base-en-v1.5"
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-base-en-v1.5')"

COPY . .

EXPOSE 8000 8501

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]