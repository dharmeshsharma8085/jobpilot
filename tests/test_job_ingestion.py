
from app.database import SessionLocal
from app.models.job import Job
from app.services.job_ingestion import ingest_job


def test_ingest_job_normalizes_and_saves():
    test_url = "https://example.com/jobpilot-ingestion-test"

    job = Job(
        title="  AI Intern  ",
        company="  JobPilot Test  ",
        location="  Remote  ",
        description="  Test description  ",
        job_url=test_url,
        source="  manual_test  ",
        employment_type="Internship",
        required_skills=[" Python ", "FastAPI", "Python"],
    )

    with SessionLocal() as db:
        try:
            saved_job = ingest_job(db, job)

            assert saved_job.title == "AI Intern"
            assert saved_job.company == "JobPilot Test"
            assert saved_job.location == "Remote"
            assert saved_job.required_skills == ["FastAPI", "Python"]
            assert saved_job.job_url == test_url
        finally:
            from sqlalchemy import delete
            from app.models.job_record import JobRecord

            db.execute(
                delete(JobRecord).where(JobRecord.job_url == test_url)
            )
            db.commit()
