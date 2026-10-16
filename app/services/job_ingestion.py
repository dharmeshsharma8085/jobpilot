
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.job_record import JobRecord
from app.repositories.job_repository import create_job


def normalize_job(job: Job) -> Job:
    """Normalize basic text fields before storing a job."""
    normalized_data = job.model_dump()

    normalized_data["title"] = job.title.strip()
    normalized_data["company"] = job.company.strip()
    normalized_data["location"] = job.location.strip() or "Not specified"
    normalized_data["description"] = job.description.strip()
    normalized_data["source"] = job.source.strip()
    normalized_data["employment_type"] = job.employment_type.strip()
    normalized_data["required_skills"] = sorted(
        {
            skill.strip()
            for skill in job.required_skills
            if skill.strip()
        },
        key=str.casefold,
    )

    return Job.model_validate(normalized_data)


def ingest_job(db: Session, job: Job) -> JobRecord:
    """Normalize and persist one validated job."""
    normalized_job = normalize_job(job)
    return create_job(db, normalized_job)
