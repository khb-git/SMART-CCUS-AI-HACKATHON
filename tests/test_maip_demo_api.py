from fastapi.testclient import TestClient

from api.main import app


def test_maip_demo_package_endpoint_returns_demo_package():
    client = TestClient(app)

    response = client.get("/demo/maip-package")

    assert response.status_code == 200

    data = response.json()

    assert data["package_name"] == "maip_demo_package"
    assert data["storage_policy"] == "Demo fixture only. No uploaded files are processed."

    report = data["report"]

    assert report["package_name"] == "maip_demo_package"
    assert report["maip_validation"]["overall_status"] == "pass"
    assert "findings" in report["maip_validation"]

    findings = {
        finding["finding_id"]: finding
        for finding in report["maip_validation"]["findings"]
    }

    assert findings["maip_evidence_present"]["status"] == "pass"
    assert findings["fracture_pressure_evidence_present"]["status"] == "pass"


def test_maip_demo_report_endpoint_returns_markdown_report():
    client = TestClient(app)

    response = client.get("/demo/maip-package/report")

    assert response.status_code == 200

    data = response.json()

    assert data["package_name"] == "maip_demo_package"
    assert data["storage_policy"] == "Demo fixture only. No uploaded files are processed."
    assert "# Class VI Package Review Report" in data["markdown"]
    assert "## MAIP Cross-Reference Validation" in data["markdown"]
    assert "proposed_maip: 1800.0 psi" in data["markdown"]
    assert "Audit Trail" in data["markdown"]


def test_maip_demo_final_packet_endpoint_returns_markdown_packet():
    client = TestClient(app)

    response = client.get("/demo/maip-package/final-packet")

    assert response.status_code == 200

    data = response.json()

    assert data["package_name"] == "maip_demo_package"
    assert data["storage_policy"] == "Demo fixture only. No uploaded files are processed."
    assert "# Class VI Final Review Packet" in data["markdown"]
    assert "## MAIP Cross-Reference Validation" in data["markdown"]
    assert "proposed_maip: 1800.0 psi" in data["markdown"]
    assert "Audit Trail" in data["markdown"]