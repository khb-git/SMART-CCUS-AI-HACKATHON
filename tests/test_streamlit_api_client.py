def test_build_ask_payload_defaults():
    from ui.api_client import build_ask_payload

    payload = build_ask_payload(
        query="How do applicants monitor injection pressure?",
        section_id="8",
    )

    assert payload["query"] == "How do applicants monitor injection pressure?"
    assert payload["section_id"] == "8"
    assert payload["intent"] == "auto"
    assert payload["k_reference"] == 3
    assert payload["k_permits"] == 5
    assert payload["expand_retrieval_query"] is True
    assert payload["use_reranking"] is True


def test_format_similarity_score():
    from ui.api_client import format_similarity_score

    assert format_similarity_score(0.785123) == "0.7851"
    assert format_similarity_score(None) == "N/A"
    assert format_similarity_score("missing") == "missing"


def test_format_evidence_heading():
    from ui.api_client import format_evidence_heading

    heading = format_evidence_heading(
        {
            "evidence_id": "E1",
            "source_label": "PERMIT PRECEDENT",
            "source_document": "One_Earth_Testing_and_Monitoring_Plan.pdf",
            "page_number": 37,
        }
    )

    assert heading == (
        "[E1] PERMIT PRECEDENT: "
        "One_Earth_Testing_and_Monitoring_Plan.pdf, p. 37"
    )


def test_ask_api_posts_to_backend(monkeypatch):
    import ui.api_client as api_client

    calls = {}

    class FakeResponse:
        def raise_for_status(self):
            calls["raise_for_status"] = True

        def json(self):
            return {
                "question": "test question",
                "answer": "test answer",
                "evidence_items": [],
            }

    def fake_post(url, json, timeout):
        calls["url"] = url
        calls["json"] = json
        calls["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(api_client.requests, "post", fake_post)

    payload = {
        "query": "test question",
    }

    response = api_client.ask_api(
        payload=payload,
        api_url="http://localhost:8000",
        timeout=10,
    )

    assert calls["url"] == "http://localhost:8000/ask"
    assert calls["json"] == payload
    assert calls["timeout"] == 10
    assert calls["raise_for_status"] is True
    assert response["answer"] == "test answer"

def test_status_label_formats_known_status():
    from ui.api_client import status_label

    assert status_label("needs_revision") == "Needs revision"
    assert status_label("mostly_complete") == "Mostly complete"
    assert status_label("present") == "Present"


def test_status_icon_formats_known_status():
    from ui.api_client import status_icon

    assert status_icon("present") == "✅"
    assert status_icon("missing") == "🔴"
    assert status_icon("unclear") == "⚪"


def test_review_document_api_posts_file_to_backend(monkeypatch):
    import ui.api_client as api_client

    calls = {}

    class FakeResponse:
        def raise_for_status(self):
            calls["raise_for_status"] = True

        def json(self):
            return {
                "document_name": "test.pdf",
                "document_type": "testing_monitoring",
                "classification_confidence": "high",
                "classification": {},
                "report": {
                    "overall_status": "mostly_complete",
                    "findings": [],
                },
                "storage_policy": "not stored",
            }

    def fake_post(url, files=None, data=None, timeout=None, json=None):
        calls["url"] = url
        calls["files"] = files
        calls["data"] = data
        calls["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(api_client.requests, "post", fake_post)

    response = api_client.review_document_api(
        file_bytes=b"%PDF fake",
        filename="test.pdf",
        plan_type="testing_monitoring",
        chunk_size=800,
        chunk_overlap=80,
        api_url="http://localhost:8000",
        timeout=10,
    )

    assert calls["url"] == "http://localhost:8000/review-document"
    assert calls["files"]["file"][0] == "test.pdf"
    assert calls["files"]["file"][1] == b"%PDF fake"
    assert calls["data"]["plan_type"] == "testing_monitoring"
    assert calls["data"]["chunk_size"] == "800"
    assert calls["data"]["chunk_overlap"] == "80"
    assert calls["timeout"] == 10
    assert calls["raise_for_status"] is True
    assert response["document_type"] == "testing_monitoring"