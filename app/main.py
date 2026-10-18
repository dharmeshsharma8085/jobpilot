from app.matching.scorer import MY_PROFILE, calculate_match_score, get_skill_gaps
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
def search_jobs(
    payload: JobSearchRequest,
    db: Session = Depends(get_db),
):
    jobs = list_jobs(db, limit=100)

    results = []

    for job in jobs:
        if payload.role and payload.role.casefold() not in job.title.casefold():
            continue

        if (
            payload.location
            and payload.location.casefold() not in job.location.casefold()
        ):
            continue

        if (
            payload.job_type
            and payload.job_type.casefold() not in job.employment_type.casefold()
        ):
            continue

        if payload.experience:
            searchable_text = f"{job.title} {job.description}".casefold()
            if payload.experience.casefold() not in searchable_text:
                continue

        score = calculate_match_score(
            job_title=job.title,
            job_location=job.location,
            job_skills=job.required_skills or [],
            profile=MY_PROFILE,
        )

        if score < payload.min_match_score:
            continue

        skill_gaps = get_skill_gaps(job.required_skills or [], MY_PROFILE)

        if payload.skills:
            requested_skills = {skill.casefold() for skill in payload.skills}
            available_skills = {
                skill.casefold()
                for skill in (job.required_skills or [])
            }
            if not requested_skills.intersection(available_skills):
                continue

        results.append(
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "job_url": job.job_url,
                "source": job.source,
                "employment_type": job.employment_type,
                "required_skills": job.required_skills,
                "match_score": score,
                **skill_gaps,
            }
        )

    results.sort(key=lambda item: item["match_score"], reverse=True)

    return {
        "filters": payload.model_dump(),
        "count": len(results),
        "jobs": results,
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
