from fastapi.testclient import TestClient


def test_review_document_endpoint_returns_gap_report(monkeypatch):
    import api.main as api_main

    calls = {}

    class FakeTemporaryDocument:
        original_filename = "testing_monitoring_plan.pdf"
        file_extension = ".pdf"
        chunks = []

    class FakeClassification:
        document_type = "testing_monitoring"
        confidence = "high"

        def to_dict(self):
            return {
                "document_type": self.document_type,
                "confidence": self.confidence,
                "matched_terms": ["testing and monitoring plan"],
                "reason": "Matched uploaded document to Testing and Monitoring Plan.",
            }

    class FakeChecklist:
        checklist_id = "testing_monitoring_v1"
        plan_type = "testing_monitoring"

    class FakeReport:
        document_name = "testing_monitoring_plan.pdf"

        def to_dict(self):
            return {
                "document_name": "testing_monitoring_plan.pdf",
                "plan_type": "testing_monitoring",
                "checklist_id": "testing_monitoring_v1",
                "overall_status": "needs_revision",
                "summary": "Checklist review complete.",
                "findings": [
                    {
                        "item_id": "injection_pressure_monitoring",
                        "label": "Injection pressure monitoring",
                        "status": "present",
                        "severity": "critical",
                        "requirement_level": "required",
                        "matched_terms": ["injection pressure"],
                        "supporting_excerpts": ["Injection pressure will be monitored."],
                        "finding": "The document appears to address pressure monitoring.",
                        "recommended_fix": "",
                    }
                ],
            }

    def fake_ingest_review_document_temporarily(
        file_path,
        chunk_size=1000,
        chunk_overlap=100,
    ):
        calls["ingest_file_path"] = str(file_path)
        calls["chunk_size"] = chunk_size
        calls["chunk_overlap"] = chunk_overlap
        return FakeTemporaryDocument()

    def fake_classify_review_document(document):
        calls["classified_document"] = document
        return FakeClassification()

    def fake_load_default_checklist(plan_type):
        calls["plan_type"] = plan_type
        return FakeChecklist()

    def fake_analyze_document_against_checklist(document, checklist):
        calls["analyzed_document"] = document
        calls["checklist"] = checklist
        return FakeReport()

    monkeypatch.setattr(
        api_main,
        "ingest_review_document_temporarily",
        fake_ingest_review_document_temporarily,
    )
    monkeypatch.setattr(
        api_main,
        "classify_review_document",
        fake_classify_review_document,
    )
    monkeypatch.setattr(
        api_main,
        "load_default_checklist",
        fake_load_default_checklist,
    )
    monkeypatch.setattr(
        api_main,
        "analyze_document_against_checklist",
        fake_analyze_document_against_checklist,
    )

    client = TestClient(api_main.app)

    response = client.post(
        "/review-document",
        files={
            "file": (
                "testing_monitoring_plan.pdf",
                b"%PDF fake",
                "application/pdf",
            )
        },
        data={
            "plan_type": "auto",
            "chunk_size": "800",
            "chunk_overlap": "80",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["document_name"] == "testing_monitoring_plan.pdf"
    assert data["document_type"] == "testing_monitoring"
    assert data["classification_confidence"] == "high"
    assert data["classification"]["document_type"] == "testing_monitoring"
    assert data["report"]["overall_status"] == "needs_revision"
    assert data["report"]["findings"][0]["item_id"] == (
        "injection_pressure_monitoring"
    )
    assert "not stored" in data["storage_policy"]

    assert calls["chunk_size"] == 800
    assert calls["chunk_overlap"] == 80
    assert calls["plan_type"] == "testing_monitoring"


def test_review_document_endpoint_rejects_unsupported_file():
    from api.main import app

    client = TestClient(app)

    response = client.post(
        "/review-document",
        files={
            "file": (
                "notes.txt",
                b"not supported",
                "text/plain",
            )
        },
        data={
            "plan_type": "auto",
        },
    )

    assert response.status_code == 400
    assert "Unsupported review file type" in response.json()["detail"]


def test_review_document_endpoint_allows_manual_plan_type(monkeypatch):
    import api.main as api_main

    calls = {}

    class FakeTemporaryDocument:
        original_filename = "unknown_name.pdf"
        file_extension = ".pdf"
        chunks = []

    class FakeClassification:
        document_type = "unknown"
        confidence = "unknown"

        def to_dict(self):
            return {
                "document_type": "unknown",
                "confidence": "unknown",
                "matched_terms": [],
                "reason": "No match.",
            }

    class FakeChecklist:
        checklist_id = "testing_monitoring_v1"
        plan_type = "testing_monitoring"

    class FakeReport:
        def to_dict(self):
            return {
                "document_name": "unknown_name.pdf",
                "plan_type": "testing_monitoring",
                "checklist_id": "testing_monitoring_v1",
                "overall_status": "incomplete",
                "summary": "Checklist review complete.",
                "findings": [],
            }

    monkeypatch.setattr(
        api_main,
        "ingest_review_document_temporarily",
        lambda *args, **kwargs: FakeTemporaryDocument(),
    )
    monkeypatch.setattr(
        api_main,
        "classify_review_document",
        lambda document: FakeClassification(),
    )

    def fake_load_default_checklist(plan_type):
        calls["plan_type"] = plan_type
        return FakeChecklist()

    monkeypatch.setattr(api_main, "load_default_checklist", fake_load_default_checklist)
    monkeypatch.setattr(
        api_main,
        "analyze_document_against_checklist",
        lambda document, checklist: FakeReport(),
    )

    client = TestClient(api_main.app)

    response = client.post(
        "/review-document",
        files={
            "file": (
                "unknown_name.pdf",
                b"%PDF fake",
                "application/pdf",
            )
        },
        data={
            "plan_type": "testing_monitoring",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["document_type"] == "testing_monitoring"
    assert data["classification"]["document_type"] == "unknown"
    assert calls["plan_type"] == "testing_monitoring"


def test_review_document_endpoint_rejects_unknown_auto_classification(monkeypatch):
    import api.main as api_main

    class FakeTemporaryDocument:
        original_filename = "unknown_name.pdf"
        file_extension = ".pdf"
        chunks = []

    class FakeClassification:
        document_type = "unknown"
        confidence = "unknown"

        def to_dict(self):
            return {
                "document_type": "unknown",
                "confidence": "unknown",
                "matched_terms": [],
                "reason": "No match.",
            }

    monkeypatch.setattr(
        api_main,
        "ingest_review_document_temporarily",
        lambda *args, **kwargs: FakeTemporaryDocument(),
    )
    monkeypatch.setattr(
        api_main,
        "classify_review_document",
        lambda document: FakeClassification(),
    )

    client = TestClient(api_main.app)

    response = client.post(
        "/review-document",
        files={
            "file": (
                "unknown_name.pdf",
                b"%PDF fake",
                "application/pdf",
            )
        },
        data={
            "plan_type": "auto",
        },
    )

    assert response.status_code == 400
    assert "Could not classify uploaded document" in response.json()["detail"]


def test_review_document_endpoint_rejects_missing_checklist(monkeypatch):
    import api.main as api_main

    class FakeTemporaryDocument:
        original_filename = "well_construction.pdf"
        file_extension = ".pdf"
        chunks = []

    class FakeClassification:
        document_type = "well_construction"
        confidence = "high"

        def to_dict(self):
            return {
                "document_type": "well_construction",
                "confidence": "high",
                "matched_terms": ["well construction plan"],
                "reason": "Matched.",
            }

    monkeypatch.setattr(
        api_main,
        "ingest_review_document_temporarily",
        lambda *args, **kwargs: FakeTemporaryDocument(),
    )
    monkeypatch.setattr(
        api_main,
        "classify_review_document",
        lambda document: FakeClassification(),
    )
    monkeypatch.setattr(
        api_main,
        "load_default_checklist",
        lambda plan_type: (_ for _ in ()).throw(FileNotFoundError()),
    )

    client = TestClient(api_main.app)

    response = client.post(
        "/review-document",
        files={
            "file": (
                "well_construction.pdf",
                b"%PDF fake",
                "application/pdf",
            )
        },
        data={
            "plan_type": "auto",
        },
    )

    assert response.status_code == 400
    assert "No review checklist is available" in response.json()["detail"]