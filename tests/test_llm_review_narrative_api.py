from fastapi.testclient import TestClient

from api.main import app
from demo_samples.maip_demo_package import build_maip_demo_package_response


def test_review_narrative_endpoint_returns_template_narrative():
    client = TestClient(app)
    package_response = build_maip_demo_package_response()

    response = client.post(
        "/review-narrative",
        json={
            "package_response": package_response,
            "reviewer_confirmations": [],
            "use_llm": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["used_llm"] is False
    assert data["model_name"] == "deterministic-template"
    assert "Backend decides" in data["boundary_notice"]
    assert "maip_demo_package" in data["narrative"]
    assert "maip_evidence_present" in data["narrative"]


def test_review_narrative_endpoint_accepts_reviewer_confirmations():
    client = TestClient(app)
    package_response = build_maip_demo_package_response()

    response = client.post(
        "/review-narrative",
        json={
            "package_response": package_response,
            "reviewer_confirmations": [
                {
                    "Required Item": "Maximum allowable injection pressure",
                    "Reviewer Confirmation": "Confirmed",
                    "Reviewer Notes": "Demo reviewer confirmed cited value.",
                }
            ],
            "use_llm": False,
        },
    )

    assert response.status_code == 200
    assert "maip_demo_package" in response.json()["narrative"]