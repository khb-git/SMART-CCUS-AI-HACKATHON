"""
Local embeddings using sentence-transformers.

Runs locally — no API calls. Class VI permit data is sensitive enough
that we should avoid sending it to a cloud embedding service.

The default model BAAI/bge-base-en-v1.5 is a strong general retrieval
model. Future work may benchmark alternatives.
"""

import logging

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "BAAI/bge-base-en-v1.5"
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class Embeddings:
    """Wraps a sentence-transformers model for embedding text.

    The model loads on first use, so creating this class is cheap. Actual model
    loading only happens when encode() or encode_query() is called.
    """

    def __init__(self, model_name=DEFAULT_MODEL):
        self.model_name = model_name
        self._model = None

    def _load(self):
        """Lazy-load the local sentence-transformers model."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required for local embeddings. "
                "Install dependencies with `pip install -r requirements.txt`."
            ) from exc

        logger.info("Loading embedding model: %s", self.model_name)
        self._model = SentenceTransformer(self.model_name)

    def encode(self, texts):
        """Embed a list of document texts.

        Args:
            texts: list of strings.

        Returns:
            list of embedding vectors, one per input text.
        """
        if isinstance(texts, str):
            raise TypeError("encode() expects a list of strings, not a single string")

        if not texts:
            return []

        self._load()

        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
        )

        return embeddings.tolist()

    def encode_query(self, text):
        """Embed a single retrieval query.

        BGE models recommend a query prefix so query embeddings are optimized
        for retrieval against passage/document embeddings.
        """
        if not isinstance(text, str):
            raise TypeError("encode_query() expects a string")

        self._load()

        prefixed = f"{BGE_QUERY_PREFIX}{text}"
        embedding = self._model.encode(
            prefixed,
            normalize_embeddings=True,
        )

        return embedding.tolist()