from sqlalchemy import text
from app.database import engine

test_url = "https://example.com/jobpilot-test-001"

with engine.begin() as connection:
    result = connection.execute(
        text("""
            INSERT INTO jobs (
                title, company, location, description,
                job_url, source, employment_type, required_skills
            )
            VALUES (
                :title, :company, :location, :description,
                :job_url, :source, :employment_type, :required_skills
            )
            RETURNING id, title, company
        """),
        {
            "title": "Test AI Intern",
            "company": "JobPilot Test",
            "location": "Remote",
            "description": "Temporary database test",
            "job_url": test_url,
            "source": "manual_test",
            "employment_type": "Internship",
            "required_skills": '["Python", "FastAPI"]',
        },
    )
    print("Inserted:", result.fetchone())

    connection.execute(
        text("DELETE FROM jobs WHERE job_url = :url"),
        {"url": test_url},
    )

    print("Test row deleted.")