import pytest


class FakeVector:
    def __init__(self, values):
        self.values = values

    def tolist(self):
        return self.values


class FakeSentenceTransformer:
    loaded_model_name = None
    encoded_inputs = []

    def __init__(self, model_name):
        FakeSentenceTransformer.loaded_model_name = model_name

    def encode(self, texts, normalize_embeddings=True):
        FakeSentenceTransformer.encoded_inputs.append(
            {
                "texts": texts,
                "normalize_embeddings": normalize_embeddings,
            }
        )

        if isinstance(texts, list):
            return FakeVector([[1.0, 0.0, 0.0] for _ in texts])

        return FakeVector([0.0, 1.0, 0.0])


def test_encode_loads_model_and_returns_vectors(monkeypatch):
    import rag.embeddings as embeddings_module

    FakeSentenceTransformer.encoded_inputs = []
    monkeypatch.setattr(
        embeddings_module,
        "SentenceTransformer",
        FakeSentenceTransformer,
        raising=False,
    )

    # Patch the import inside _load by placing fake class in module namespace.
    def fake_load(self):
        if self._model is None:
            self._model = FakeSentenceTransformer(self.model_name)

    monkeypatch.setattr(embeddings_module.Embeddings, "_load", fake_load)

    embedder = embeddings_module.Embeddings(model_name="fake-model")
    vectors = embedder.encode(["first chunk", "second chunk"])

    assert vectors == [[1.0, 0.0, 0.0], [1.0, 0.0, 0.0]]
    assert embedder._model is not None


def test_encode_empty_list_returns_empty_list():
    from rag.embeddings import Embeddings

    embedder = Embeddings(model_name="fake-model")

    assert embedder.encode([]) == []


def test_encode_rejects_single_string():
    from rag.embeddings import Embeddings

    embedder = Embeddings(model_name="fake-model")

    with pytest.raises(TypeError, match="list of strings"):
        embedder.encode("not a list")


def test_encode_query_adds_bge_prefix(monkeypatch):
    import rag.embeddings as embeddings_module

    FakeSentenceTransformer.encoded_inputs = []

    def fake_load(self):
        if self._model is None:
            self._model = FakeSentenceTransformer(self.model_name)

    monkeypatch.setattr(embeddings_module.Embeddings, "_load", fake_load)

    embedder = embeddings_module.Embeddings(model_name="fake-model")
    vector = embedder.encode_query("What does the regulation require for MAIP?")

    assert vector == [0.0, 1.0, 0.0]

    encoded_text = FakeSentenceTransformer.encoded_inputs[-1]["texts"]
    assert encoded_text.startswith(
        "Represent this sentence for searching relevant passages: "
    )
    assert "MAIP" in encoded_text


def test_encode_query_rejects_non_string():
    from rag.embeddings import Embeddings

    embedder = Embeddings(model_name="fake-model")

    with pytest.raises(TypeError, match="expects a string"):
        embedder.encode_query(["not", "a", "string"])