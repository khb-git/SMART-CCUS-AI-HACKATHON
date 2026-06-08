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

def test_report_export_helpers_are_available_from_ui_client():
    from ui.api_client import build_markdown_review_report, default_report_filename

    assert callable(build_markdown_review_report)
    assert default_report_filename("test.pdf") == "test_review_report.md"

def test_review_package_api_posts_multiple_files_to_backend(monkeypatch):
    import ui.api_client as api_client

    calls = {}

    class FakeResponse:
        def raise_for_status(self):
            calls["raise_for_status"] = True

        def json(self):
            return {
                "package_name": "adm_package",
                "report": {
                    "overall_status": "missing_required_documents",
                    "summary": "Package review complete.",
                    "detected_plan_types": ["testing_monitoring"],
                    "missing_required_plan_types": ["well_construction"],
                    "missing_expected_plan_types": ["well_construction"],
                    "duplicate_plan_types": [],
                    "unknown_documents": [],
                    "document_reviews": [],
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

    response = api_client.review_package_api(
        files=[
            ("testing_monitoring.pdf", b"%PDF fake 1"),
            ("well_construction.pdf", b"%PDF fake 2"),
        ],
        package_name="adm_package",
        chunk_size=800,
        chunk_overlap=80,
        api_url="http://localhost:8000",
        timeout=20,
    )

    assert calls["url"] == "http://localhost:8000/review-package"
    assert len(calls["files"]) == 2
    assert calls["files"][0][0] == "files"
    assert calls["files"][0][1][0] == "testing_monitoring.pdf"
    assert calls["files"][0][1][1] == b"%PDF fake 1"
    assert calls["files"][1][1][0] == "well_construction.pdf"
    assert calls["data"]["package_name"] == "adm_package"
    assert calls["data"]["chunk_size"] == "800"
    assert calls["data"]["chunk_overlap"] == "80"
    assert calls["timeout"] == 20
    assert calls["raise_for_status"] is True
    assert response["report"]["overall_status"] == "missing_required_documents"

def test_package_report_export_helpers_are_available_from_ui_client():
    from ui.api_client import (
        build_markdown_package_report,
        default_package_report_filename,
    )

    assert callable(build_markdown_package_report)
    assert (
        default_package_report_filename("test package")
        == "test_package_package_review_report.md"
    )