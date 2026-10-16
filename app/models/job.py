
from datetime import datetime, timezone
from pydantic import BaseModel, Field, HttpUrl


class Job(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    company: str = Field(min_length=1, max_length=200)
    location: str = "Not specified"
    description: str = ""
    job_url: HttpUrl
    source: str = Field(min_length=1, max_length=100)
    employment_type: str = "Internship"
    required_skills: list[str] = Field(default_factory=list)
    posted_at: datetime | None = None
    discovered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
