from fastapi.testclient import TestClient

from api.main import app


def test_maip_demo_package_smoke_has_review_ready_content():
    client = TestClient(app)

    response = client.get("/demo/maip-package")

    assert response.status_code == 200

    data = response.json()
    report = data["report"]

    assert data["package_name"] == "maip_demo_package"
    assert data["storage_policy"] == "Demo fixture only. No uploaded files are processed."

    assert report["package_name"] == "maip_demo_package"
    assert report["overall_status"] in {
        "review_ready",
        "mostly_complete",
        "needs_review",
        "needs_revision",
        "incomplete",
    }
    assert report["maip_validation"]["overall_status"] == "pass"

    document_reviews = report.get("document_reviews", [])
    assert document_reviews

    detected_plan_types = set(report.get("detected_plan_types", []))
    assert "site_operating" in detected_plan_types
    assert "testing_monitoring" in detected_plan_types
    assert "aor_corrective_action" in detected_plan_types


def test_maip_demo_package_report_smoke_has_reviewer_sections():
    client = TestClient(app)

    response = client.get("/demo/maip-package/report")

    assert response.status_code == 200

    data = response.json()
    markdown = data["markdown"]

    assert data["package_name"] == "maip_demo_package"
    assert "# Class VI Package Review Report" in markdown
    assert "## Reviewer Disclaimers" in markdown
    assert "not a final regulatory determination" in markdown
    assert "## Reviewer Priority Summary" in markdown
    assert "## Package Review Metrics" in markdown
    assert "## Reviewer Action Items" in markdown
    assert "## MAIP Cross-Reference Validation" in markdown
    assert "## Completeness Checklist Review" in markdown
    assert "## Package Coverage Evidence" in markdown
    assert "## Known Limitations" in markdown
    assert "proposed_maip: 1800.0 psi" in markdown
    assert "Audit Trail" in markdown


def test_maip_demo_final_packet_smoke_has_regulator_ready_sections():
    client = TestClient(app)

    response = client.get("/demo/maip-package/final-packet")

    assert response.status_code == 200

    data = response.json()
    markdown = data["markdown"]

    assert data["package_name"] == "maip_demo_package"
    assert "# Class VI Final Review Packet" in markdown
    assert "## Packet Purpose" in markdown
    assert "## Reviewer Disclaimers" in markdown
    assert "not a final regulatory determination" in markdown
    assert "## Final Package Summary" in markdown
    assert "## Package Review Metrics" in markdown
    assert "## Reviewer Action Items" in markdown
    assert "## MAIP Cross-Reference Validation" in markdown
    assert "## Deficiency Table" in markdown
    assert "## Completeness Checklist Review" in markdown
    assert "## Known Limitations" in markdown
    assert "## Reviewer Sign-Off" in markdown
    assert "## Appendix: Full Package Review Report" in markdown
    assert "proposed_maip: 1800.0 psi" in markdown
    assert "Audit Trail" in markdown


def test_maip_demo_report_and_final_packet_share_core_boundaries():
    client = TestClient(app)

    report_response = client.get("/demo/maip-package/report")
    packet_response = client.get("/demo/maip-package/final-packet")

    assert report_response.status_code == 200
    assert packet_response.status_code == 200

    report_markdown = report_response.json()["markdown"]
    packet_markdown = packet_response.json()["markdown"]

    required_boundary_phrases = [
        "reviewer-support tool",
        "qualified reviewer",
        "OCR-derived evidence is based on visible text only",
        "does not inspect, recover, or infer hidden content",
        "does not replace legal, engineering, or regulatory judgment",
    ]

    for phrase in required_boundary_phrases:
        assert phrase in report_markdown
        assert phrase in packet_markdown