
from datetime import datetime
from typing import Any

import requests

from app.models.job import Job

REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"
REQUEST_TIMEOUT = 20


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _map_job(item: dict[str, Any]) -> Job | None:
    """Convert a Remotive API listing into JobPilot's Job schema."""
    title = str(item.get("title") or "").strip()
    company = str(item.get("company_name") or "").strip()
    url = str(item.get("url") or "").strip()

    if not title or not company or not url:
        return None

    tags = item.get("tags") or []
    skills = [
        str(tag).strip()
        for tag in tags
        if str(tag).strip()
    ]

    raw_type = str(item.get("job_type") or "").lower()
    employment_types = {
        "full_time": "Full-time",
        "part_time": "Part-time",
        "contract": "Contract",
        "freelance": "Freelance",
        "internship": "Internship",
    }

    return Job(
        title=title,
        company=company,
        location=str(
            item.get("candidate_required_location") or "Remote"
        ).strip(),
        description=str(item.get("description") or ""),
        job_url=url,
        source="Remotive",
        employment_type=employment_types.get(raw_type, "Not specified"),
        required_skills=skills,
        posted_at=_parse_date(item.get("publication_date")),
    )


def fetch_remotive_jobs(
    search: str | None = None,
    limit: int = 25,
) -> list[Job]:
    """Fetch a limited batch of remote jobs from Remotive."""
    params: dict[str, str | int] = {"limit": limit}

    if search and search.strip():
        params["search"] = search.strip()

    response = requests.get(
        REMOTIVE_API_URL,
        params=params,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    payload = response.json()
    items = payload.get("jobs", [])

    if not isinstance(items, list):
        raise ValueError("Unexpected response format from Remotive API.")

    jobs: list[Job] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        try:
            job = _map_job(item)
            if job:
                jobs.append(job)
        except (ValueError, TypeError):
            continue

    return jobs
