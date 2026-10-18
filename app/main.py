
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.job import Job
from app.services.job_ingestion import ingest_job
from app.repositories.job_repository import list_jobs

app = FastAPI(title="JobPilot AI", version="0.1.0")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class JobCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    company: str = Field(min_length=1, max_length=200)
    location: str = "Not specified"
    description: str = ""
    job_url: HttpUrl
    source: str = Field(min_length=1, max_length=100)
    employment_type: str = "Internship"
    required_skills: list[str] = Field(default_factory=list)


class JobSearchRequest(BaseModel):
    role: str = Field(default="", max_length=200)
    location: str = Field(default="", max_length=200)
    experience: str = Field(default="", max_length=100)
    job_type: str = Field(default="", max_length=100)
    skills: list[str] = Field(default_factory=list)
    min_match_score: int = Field(default=0, ge=0, le=100)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "JobPilot AI"}


@app.post("/jobs/search")
def search_jobs(payload: JobSearchRequest):
    return {
        "filters": payload.model_dump(),
        "jobs": [],
        "message": "Search filters validated. Job matching integration is the next step.",
    }


@app.post("/jobs", status_code=201)
def create_job_endpoint(
    payload: JobCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        job = Job.model_validate(payload.model_dump())
        saved_job = ingest_job(db, job)
        return {
            "id": saved_job.id,
            "title": saved_job.title,
            "company": saved_job.company,
            "job_url": saved_job.job_url,
            "required_skills": saved_job.required_skills,
        }
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to save job. Check application logs.",
        ) from exc


@app.get("/jobs")
def get_jobs(
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    jobs = list_jobs(db, limit=limit)
    return [
        {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "job_url": job.job_url,
            "source": job.source,
            "required_skills": job.required_skills,
            "match_score": job.match_score,
        }
        for job in jobs
    ]
