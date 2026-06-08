from fastapi.testclient import TestClient


def test_review_package_endpoint_returns_package_report(monkeypatch):
    import api.main as api_main

    calls = {}

    class FakeTemporaryDocument:
        def __init__(self, name):
            self.original_filename = name
            self.file_extension = ".pdf"
            self.chunks = []

    class FakePackageReport:
        def to_dict(self):
            return {
                "package_name": "adm_package",
                "overall_status": "missing_required_documents",
                "summary": "Package review complete.",
                "expected_plan_types": ["testing_monitoring", "well_construction"],
                "required_plan_types": ["testing_monitoring", "well_construction"],
                "detected_plan_types": ["testing_monitoring"],
                "missing_required_plan_types": ["well_construction"],
                "missing_expected_plan_types": ["well_construction"],
                "duplicate_plan_types": [],
                "unknown_documents": [],
                "document_reviews": [
                    {
                        "document_name": "testing_monitoring.pdf",
                        "document_type": "testing_monitoring",
                        "classification_confidence": "high",
                        "classification": {
                            "document_type": "testing_monitoring",
                            "confidence": "high",
                            "matched_terms": ["testing and monitoring plan"],
                            "reason": "Matched.",
                        },
                        "report": {
                            "overall_status": "mostly_complete",
                            "summary": "Checklist review complete.",
                            "findings": [],
                        },
                        "error": "",
                    }
                ],
            }

    def fake_ingest_review_document_temporarily(
        file_path,
        chunk_size=1000,
        chunk_overlap=100,
    ):
        calls.setdefault("ingested_files", []).append(str(file_path))
        calls["chunk_size"] = chunk_size
        calls["chunk_overlap"] = chunk_overlap
        return FakeTemporaryDocument(name=file_path.name)

    def fake_review_document_package(documents, package_name="uploaded_package"):
        calls["document_count"] = len(documents)
        calls["package_name"] = package_name
        return FakePackageReport()

    monkeypatch.setattr(
        api_main,
        "ingest_review_document_temporarily",
        fake_ingest_review_document_temporarily,
    )
    monkeypatch.setattr(
        api_main,
        "review_document_package",
        fake_review_document_package,
    )

    client = TestClient(api_main.app)

    response = client.post(
        "/review-package",
        files=[
            (
                "files",
                (
                    "testing_monitoring.pdf",
                    b"%PDF fake 1",
                    "application/pdf",
                ),
            ),
            (
                "files",
                (
                    "well_construction.pdf",
                    b"%PDF fake 2",
                    "application/pdf",
                ),
            ),
        ],
        data={
            "package_name": "adm_package",
            "chunk_size": "800",
            "chunk_overlap": "80",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["package_name"] == "adm_package"
    assert data["report"]["overall_status"] == "missing_required_documents"
    assert data["report"]["missing_required_plan_types"] == ["well_construction"]
    assert "not stored" in data["storage_policy"]

    assert calls["document_count"] == 2
    assert calls["package_name"] == "adm_package"
    assert calls["chunk_size"] == 800
    assert calls["chunk_overlap"] == 80


def test_review_package_endpoint_rejects_unsupported_file():
    from api.main import app

    client = TestClient(app)

    response = client.post(
        "/review-package",
        files=[
            (
                "files",
                (
                    "notes.txt",
                    b"not supported",
                    "text/plain",
                ),
            )
        ],
        data={
            "package_name": "bad_package",
        },
    )

    assert response.status_code == 400
    assert "Unsupported review file type" in response.json()["detail"]


def test_review_package_endpoint_handles_ingestion_error(monkeypatch):
    import api.main as api_main

    def fake_ingest_review_document_temporarily(*args, **kwargs):
        raise RuntimeError("bad upload")

    monkeypatch.setattr(
        api_main,
        "ingest_review_document_temporarily",
        fake_ingest_review_document_temporarily,
    )

    client = TestClient(api_main.app)

    response = client.post(
        "/review-package",
        files=[
            (
                "files",
                (
                    "testing_monitoring.pdf",
                    b"%PDF fake",
                    "application/pdf",
                ),
            )
        ],
        data={
            "package_name": "bad_package",
        },
    )

    assert response.status_code == 500
    assert "Temporary review ingestion failed" in response.json()["detail"]


def test_review_package_endpoint_handles_package_review_error(monkeypatch):
    import api.main as api_main

    class FakeTemporaryDocument:
        original_filename = "testing_monitoring.pdf"
        file_extension = ".pdf"
        chunks = []

    monkeypatch.setattr(
        api_main,
        "ingest_review_document_temporarily",
        lambda *args, **kwargs: FakeTemporaryDocument(),
    )

    def fake_review_document_package(*args, **kwargs):
        raise RuntimeError("package failure")

    monkeypatch.setattr(
        api_main,
        "review_document_package",
        fake_review_document_package,
    )

    client = TestClient(api_main.app)

    response = client.post(
        "/review-package",
        files=[
            (
                "files",
                (
                    "testing_monitoring.pdf",
                    b"%PDF fake",
                    "application/pdf",
                ),
            )
        ],
        data={
            "package_name": "bad_package",
        },
    )

    assert response.status_code == 500
    assert "Package review failed" in response.json()["detail"]

def test_review_package_openapi_treats_files_as_binary_uploads():
    from api.main import app

    schema = app.openapi()
    request_body = schema["paths"]["/review-package"]["post"]["requestBody"]
    multipart_schema = request_body["content"]["multipart/form-data"]["schema"]

    schema_name = multipart_schema["$ref"].split("/")[-1]
    body_schema = schema["components"]["schemas"][schema_name]

    files_property = body_schema["properties"]["files"]

    assert files_property["type"] == "array"
    assert files_property["items"]["type"] == "string"
    assert files_property["items"]["format"] == "binary"