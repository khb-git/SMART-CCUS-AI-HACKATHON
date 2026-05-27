"""
Local embeddings using sentence-transformers.

Runs locally — no API calls. Class VI permit data is sensitive enough
that we can't send it to a cloud embedding service.

The default model BAAI/bge-base-en-v1.5 is a strong general retrieval
model. Phase 2 may benchmark alternatives.
"""

import logging

logger = logging.getLogger(__name__)


DEFAULT_MODEL = "BAAI/bge-base-en-v1.5"


class Embeddings:
    """Wraps a sentence-transformers model for embedding text.

    The model loads on first use (lazy), so creating one of these is cheap.
    """

    def __init__(self, model_name=DEFAULT_MODEL):
        self.model_name = model_name
        self._model = None

    def _load(self):
        if self._model is not None:
            return
        # TODO: from sentence_transformers import SentenceTransformer
        #       self._model = SentenceTransformer(self.model_name)
        logger.warning("Embeddings._load not yet implemented")

    def encode(self, texts):
        """Embed a list of document texts. Returns one vector per text."""
        self._load()
        # TODO: return self._model.encode(texts, normalize_embeddings=True).tolist()
        return [[] for _ in texts]

    def encode_query(self, text):
        """Embed a single query string.

        BGE models recommend a prefix for queries — kept separate from
        encode() so we can't accidentally embed queries like documents.
        """
        self._load()
        # TODO: prefixed = f"Represent this sentence for searching relevant passages: {text}"
        #       return self._model.encode(prefixed, normalize_embeddings=True).tolist()
        return []
