
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "JobPilot AI",
    }


def test_job_search():
    response = client.post(
        "/jobs/search",
        json={
            "role": "AI Engineer",
            "location": "Remote",
            "experience": "Internship",
            "job_type": "Internship",
            "skills": ["Python", "FastAPI", "RAG"],
            "min_match_score": 70,
        },
    )

    assert response.status_code == 200
    assert response.json()["filters"]["role"] == "AI Engineer"
    assert response.json()["filters"]["min_match_score"] == 70


def test_invalid_match_score():
    response = client.post(
        "/jobs/search",
        json={
            "role": "AI Engineer",
            "min_match_score": 150,
        },
    )

    assert response.status_code == 422
