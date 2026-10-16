
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.job_record import JobRecord


def get_job_by_url(db: Session, job_url: str) -> JobRecord | None:
    statement = select(JobRecord).where(JobRecord.job_url == job_url)
    return db.scalar(statement)


def create_job(db: Session, job: Job) -> JobRecord:
    existing_job = get_job_by_url(db, str(job.job_url))

    if existing_job:
        return existing_job

    job_record = JobRecord(
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        job_url=str(job.job_url),
        source=job.source,
        employment_type=job.employment_type,
        required_skills=job.required_skills,
        posted_at=job.posted_at,
        discovered_at=job.discovered_at,
    )

    db.add(job_record)
    db.commit()
    db.refresh(job_record)

    return job_record


def list_jobs(db: Session, limit: int = 50) -> list[JobRecord]:
    statement = (
        select(JobRecord)
        .order_by(JobRecord.discovered_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement).all())
