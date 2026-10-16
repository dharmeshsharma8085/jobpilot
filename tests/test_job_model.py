
import pytest
from pydantic import ValidationError

from app.models.job import Job


def test_valid_job():
    job = Job(
        title="AI Engineer Intern",
        company="Example AI",
        job_url="https://example.com/jobs/123",
        source="company_careers",
        required_skills=["Python", "FastAPI", "RAG"],
    )

    assert job.title == "AI Engineer Intern"
    assert job.company == "Example AI"
    assert job.location == "Not specified"
    assert job.discovered_at is not None


def test_invalid_job_url():
    with pytest.raises(ValidationError):
        Job(
            title="AI Engineer Intern",
            company="Example AI",
            job_url="not-a-valid-url",
            source="company_careers",
        )


def test_missing_required_fields():
    with pytest.raises(ValidationError):
        Job(
            title="AI Engineer Intern",
            job_url="https://example.com/jobs/123",
            source="company_careers",
        )

