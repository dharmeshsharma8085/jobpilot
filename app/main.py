
import logging

from app.repositories.job_repository import get_job_by_url
from app.services.remotive_client import fetch_remotive_jobs
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.matching.scorer import (
    CandidateProfile,
    MY_PROFILE,
    calculate_match_breakdown,
)
from app.models.job import Job
from app.profile.repository import get_profile, save_profile
from app.profile.schemas import ProfileSettings, ProfileResponse
from app.repositories.job_repository import list_jobs
from app.services.job_ingestion import ingest_job


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


@app.get("/profile", response_model=ProfileResponse)
def read_profile(db: Session = Depends(get_db)):
    profile = get_profile(db)

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Candidate profile not found. Save your profile first.",
        )

    return profile


@app.put("/profile", response_model=ProfileResponse)
def update_profile(
    payload: ProfileSettings,
    db: Session = Depends(get_db),
):
    try:
        return save_profile(db, payload)
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to save candidate profile")
        raise HTTPException(
            status_code=500,
            detail="Unable to save candidate profile. Check application logs.",
        ) from exc


@app.post("/jobs/search")
def search_jobs(
    payload: JobSearchRequest,
    db: Session = Depends(get_db),
):
    try:
        jobs = list_jobs(db, limit=100)
        saved_profile = get_profile(db)

        if saved_profile is not None:
            active_profile = CandidateProfile(
                target_roles=saved_profile.target_roles or [],
                skills=saved_profile.skills or [],
                preferred_locations=saved_profile.preferred_locations or [],
                projects=saved_profile.projects or [],
                preferred_employment_types=(
                    saved_profile.preferred_employment_types or []
                ),
            )
        else:
            active_profile = MY_PROFILE

        results = []

        for job in jobs:
            title = job.title or ""
            location = job.location or ""
            description = job.description or ""
            employment_type = job.employment_type or ""
            required_skills = job.required_skills or []

            if (
                payload.role
                and payload.role.casefold() not in title.casefold()
            ):
                continue

            if (
                payload.location
                and payload.location.casefold() not in location.casefold()
            ):
                continue

            if (
                payload.job_type
                and payload.job_type.casefold()
                not in employment_type.casefold()
            ):
                continue

            if payload.experience:
                searchable_text = f"{title} {description}".casefold()
                if payload.experience.casefold() not in searchable_text:
                    continue

            match = calculate_match_breakdown(
                job_title=title,
                job_location=location,
                job_skills=required_skills,
                profile=active_profile,
                description=description,
                employment_type=employment_type,
                posted_at=job.posted_at,
            )

            score = match["match_score"]

            if score < payload.min_match_score:
                continue

            if payload.skills:
                requested_skills = {
                    skill.strip().casefold()
                    for skill in payload.skills
                    if skill.strip()
                }
                available_skills = {
                    skill.strip().casefold()
                    for skill in required_skills
                    if isinstance(skill, str) and skill.strip()
                }

                if requested_skills and not requested_skills.intersection(
                    available_skills
                ):
                    continue

            results.append(
                {
                    "id": job.id,
                    "title": title,
                    "company": job.company,
                    "location": location,
                    "job_url": str(job.job_url),
                    "source": job.source,
                    "employment_type": employment_type,
                    "required_skills": required_skills,
                    "match_score": score,
                    "rubric_version": match["rubric_version"],
                    "score_breakdown": match["score_breakdown"],
                    "unknown_signals": match["unknown_signals"],
                    "matched_skills": match["matched_skills"],
                    "missing_skills": match["missing_skills"],
                }
            )

        results.sort(
            key=lambda item: item["match_score"],
            reverse=True,
        )

        return {
            "filters": payload.model_dump(),
            "count": len(results),
            "jobs": results,
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Job search failed")
        raise HTTPException(
            status_code=500,
            detail="Job search failed. Check application logs for the cause.",
        ) from exc



@app.post("/jobs/ingest/remotive")
def ingest_remotive_endpoint(
    search: str = Query(default="AI", min_length=1, max_length=100),
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Fetch remote jobs from Remotive and save them to PostgreSQL."""
    try:
        remote_jobs = fetch_remotive_jobs(search=search, limit=limit)

        imported = 0
        duplicates = 0
        invalid = 0

        for job in remote_jobs:
            existing = get_job_by_url(db, str(job.job_url))

            if existing:
                duplicates += 1
                continue

            try:
                saved_job = ingest_job(db, job)
                if saved_job:
                    imported += 1
            except Exception:
                db.rollback()
                invalid += 1
                logger.exception(
                    "Failed to save a Remotive job: %s",
                    job.job_url,
                )

        return {
            "source": "Remotive",
            "search": search,
            "fetched": len(remote_jobs),
            "imported": imported,
            "duplicates_skipped": duplicates,
            "failed": invalid,
            "message": "Job ingestion completed.",
        }

    except Exception as exc:
        db.rollback()
        logger.exception("Remotive ingestion failed")
        raise HTTPException(
            status_code=502,
            detail="Unable to fetch jobs from Remotive. Check application logs.",
        ) from exc



@app.post("/jobs", status_code=201)
def create_job_endpoint(
    payload: JobCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        # Job is a SQLAlchemy model, so instantiate it directly.
        job = Job(
            title=payload.title,
            company=payload.company,
            location=payload.location,
            description=payload.description,
            job_url=str(payload.job_url),
            source=payload.source,
            employment_type=payload.employment_type,
            required_skills=payload.required_skills,
        )

        saved_job = ingest_job(db, job)

        return {
            "id": saved_job.id,
            "title": saved_job.title,
            "company": saved_job.company,
            "job_url": str(saved_job.job_url),
            "required_skills": saved_job.required_skills or [],
        }

    except Exception as exc:
        db.rollback()
        logger.exception("Failed to create job")
        raise HTTPException(
            status_code=500,
            detail="Unable to save job. Check application logs.",
        ) from exc


@app.get("/jobs")
def get_jobs(
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        jobs = list_jobs(db, limit=limit)

        return [
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "job_url": str(job.job_url),
                "source": job.source,
                "required_skills": job.required_skills or [],
                "match_score": job.match_score,
            }
            for job in jobs
        ]

    except Exception as exc:
        logger.exception("Failed to retrieve jobs")
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve jobs. Check application logs.",
        ) from exc
