from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)


def make_package_response():
    return {
        "package_name": "uploaded_package",
        "report": {
            "package_name": "uploaded_package",
            "detected_plan_types": ["project_narrative"],
            "document_reviews": [
                {
                    "document_name": "Project_Narrative.pdf",
                    "checklist_reports": {
                        "project_narrative": {
                            "findings": [
                                {
                                    "item_id": "permit_activities_listing",
                                    "label": (
                                        "A listing of the activities conducted "
                                        "by the applicant which require RCRA, "
                                        "UIC, NPDES, or PSD permits."
                                    ),
                                    "finding": (
                                        "The project narrative lists activities "
                                        "requiring UIC and NPDES permits."
                                    ),
                                    "matched_terms": ["UIC", "NPDES"],
                                    "confidence": "High",
                                    "evidence_locations": [
                                        {
                                            "file_name": "Project_Narrative.pdf",
                                            "page_number": 12,
                                            "excerpt": (
                                                "Activities require UIC and NPDES "
                                                "permits."
                                            ),
                                        }
                                    ],
                                }
                            ]
                        }
                    },
                }
            ],
        },
    }


def test_populated_checklist_endpoint_returns_json():
    response = client.post(
        "/populated-checklist",
        json={
            "package_response": make_package_response(),
            "plan_types": ["project_narrative"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["package_name"] == "uploaded_package"
    assert "populated_checklist" in data
    assert data["storage_policy"]

    populated = data["populated_checklist"]

    assert populated["package_name"] == "uploaded_package"
    assert populated["rows"]
    assert populated["section_summaries"]

    first_row = populated["rows"][0]

    assert first_row["section_title"]
    assert first_row["checklist_item"]
    assert first_row["reviewer_confirmation"] == "pending_review"


def test_populated_checklist_markdown_endpoint_returns_markdown():
    response = client.post(
        "/populated-checklist/markdown",
        json={
            "package_response": make_package_response(),
            "plan_types": ["project_narrative"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["package_name"] == "uploaded_package"
    assert "markdown" in data
    assert "# Populated Class VI Completeness Checklist" in data["markdown"]
    assert "Project_Narrative.pdf" in data["markdown"]
    assert "## Section Summary" in data["markdown"]


def test_populated_checklist_endpoint_rejects_unknown_plan_type():
    response = client.post(
        "/populated-checklist",
        json={
            "package_response": make_package_response(),
            "plan_types": ["not_a_real_plan_type"],
        },
    )

    assert response.status_code == 400
    assert "No supported checklists" in response.json()["detail"]