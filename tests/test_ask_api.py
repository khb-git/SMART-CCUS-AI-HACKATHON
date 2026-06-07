from fastapi.testclient import TestClient


def test_health_endpoint():
    from api.main import app

    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "class-vi-review-assistant"


def test_ask_endpoint_returns_review_answer(monkeypatch):
    import api.main as api_main

    calls = {}

    class FakeReviewAnswer:
        def to_dict(self):
            return {
                "question": "How do applicants monitor injection pressure?",
                "answer": "Based on the retrieved evidence...",
                "evidence_summary": "[E1] PERMIT PRECEDENT: test.pdf",
                "reviewer_interpretation": "Review interpretation.",
                "potential_follow_up": "Potential follow-up.",
                "evidence_items": [
                    {
                        "evidence_id": "E1",
                        "collection": "permits",
                        "source_document": "test.pdf",
                    }
                ],
            }

    def fake_ask_question(**kwargs):
        calls.update(kwargs)
        return FakeReviewAnswer()

    monkeypatch.setattr(api_main, "ask_question", fake_ask_question)

    client = TestClient(api_main.app)

    response = client.post(
        "/ask",
        json={
            "query": "How do applicants monitor injection pressure?",
            "persist_directory": "fake_chroma",
            "section_id": "8",
            "intent": "permit_precedent",
            "k_reference": 2,
            "k_permits": 4,
            "fetch_k": 20,
            "max_per_source": 1,
            "expand_retrieval_query": True,
            "use_reranking": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["question"] == "How do applicants monitor injection pressure?"
    assert data["answer"] == "Based on the retrieved evidence..."
    assert data["evidence_items"][0]["evidence_id"] == "E1"

    assert calls["question"] == "How do applicants monitor injection pressure?"
    assert calls["persist_directory"] == "fake_chroma"
    assert calls["section_id"] == "8"
    assert calls["intent"] == "permit_precedent"
    assert calls["k_reference"] == 2
    assert calls["k_permits"] == 4
    assert calls["fetch_k"] == 20
    assert calls["max_per_source"] == 1
    assert calls["expand_retrieval_query"] is True
    assert calls["use_reranking"] is True


def test_ask_endpoint_rejects_empty_query():
    from api.main import app

    client = TestClient(app)

    response = client.post(
        "/ask",
        json={
            "query": "",
        },
    )

    assert response.status_code == 422