
from dataclasses import dataclass, field
from datetime import datetime, timezone
import re


RUBRIC_VERSION = "1.0"

WEIGHTS = {
    "skills": 35,
    "role_level": 20,
    "project_relevance": 15,
    "location_work_mode": 10,
    "freshness": 10,
    "eligibility_compensation": 10,
}


@dataclass(frozen=True)
class CandidateProfile:
    target_roles: list[str]
    skills: list[str]
    preferred_locations: list[str]
    projects: list[str] = field(default_factory=list)
    preferred_employment_types: list[str] = field(
        default_factory=lambda: ["Internship"]
    )


# Canonical names allow equivalent skill terms to match.
SKILL_ALIASES = {
    "llms": "large language models",
    "llm": "large language models",
    "large language models": "large language models",
    "gen ai": "generative ai",
    "genai": "generative ai",
    "ml": "machine learning",
    "sklearn": "scikit-learn",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "lang graph": "langgraph",
    "fast api": "fastapi",
}


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


def _canonical_skill(value: str) -> str:
    normalized = _normalize_text(value)
    return SKILL_ALIASES.get(normalized, normalized)


def _normalize_skills(values: list[str]) -> set[str]:
    return {
        _canonical_skill(value)
        for value in values
        if value.strip()
    }


def get_skill_gaps(
    job_skills: list[str],
    profile: CandidateProfile,
) -> dict[str, list[str]]:
    """Return unique matched and missing required skills."""
    candidate_skills = _normalize_skills(profile.skills)
    matched, missing, seen = [], [], set()

    for skill in job_skills:
        display = skill.strip()
        if not display:
            continue

        canonical = _canonical_skill(display)
        if canonical in seen:
            continue
        seen.add(canonical)

        if canonical in candidate_skills:
            matched.append(display)
        else:
            missing.append(display)

    return {
        "matched_skills": matched,
        "missing_skills": missing,
    }


def _role_score(
    job_title: str,
    employment_type: str | None,
    profile: CandidateProfile,
) -> int:
    title = _normalize_text(job_title)
    roles = [_normalize_text(role) for role in profile.target_roles if role.strip()]

    role_match = any(role in title for role in roles)
    if not role_match:
        return 0

    score = 15

    # Award the remaining five points only when level/type is supported.
    if employment_type:
        preferred = {
            _normalize_text(item)
            for item in profile.preferred_employment_types
        }
        actual = _normalize_text(employment_type)
        if actual in preferred:
            score += 5

    return score


def calculate_match_breakdown(
    job_title: str,
    job_location: str,
    job_skills: list[str],
    profile: CandidateProfile,
    *,
    description: str = "",
    employment_type: str | None = None,
    posted_at: datetime | None = None,
    now: datetime | None = None,
    eligibility_match: bool | None = None,
    compensation_match: bool | None = None,
) -> dict:
    """
    Return a transparent 100-point rubric breakdown.

    Unknown signals earn no points and are explicitly reported.
    The score is a decision aid, not a hiring probability.
    """
    earned = {}
    unknown = []

    # 1. Skills: 35 points
    required = _normalize_skills(job_skills)
    candidate = _normalize_skills(profile.skills)

    if required:
        earned["skills"] = round(
            35 * len(required & candidate) / len(required)
        )
    else:
        earned["skills"] = 0
        unknown.append("skills: no required skills provided")

    # 2. Role / level fit: 20 points
    if job_title.strip():
        earned["role_level"] = _role_score(
            job_title, employment_type, profile
        )
    else:
        earned["role_level"] = 0
        unknown.append("role_level: job title unavailable")

    # 3. Project relevance: 15 points
    # Use only projects explicitly provided in the verified profile.
    if profile.projects and description.strip():
        project_terms = set(
            re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#.-]{1,}\b",
                       " ".join(profile.projects).casefold())
        )
        job_terms = set(
            re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#.-]{1,}\b",
                       description.casefold())
        )
        overlap = project_terms & job_terms
        earned["project_relevance"] = round(
            15 * len(overlap) / len(job_terms)
        ) if job_terms else 0
    else:
        earned["project_relevance"] = 0
        unknown.append("project_relevance: project or job description unavailable")

    # 4. Location / work mode: 10 points
    if job_location.strip() and _normalize_text(job_location) not in {
        "not specified", "unknown", "n/a"
    }:
        location = _normalize_text(job_location)
        location_match = any(
            _normalize_text(preference) in location
            for preference in profile.preferred_locations
            if preference.strip()
        )
        earned["location_work_mode"] = 10 if location_match else 0
    else:
        earned["location_work_mode"] = 0
        unknown.append("location_work_mode: job location unavailable")

    # 5. Freshness / active status: 10 points
    # Use the verified posting date only; discovery date is not a posting date.
    if posted_at is not None:
        current = now or datetime.now(timezone.utc)
        posted = posted_at
        if posted.tzinfo is None:
            posted = posted.replace(tzinfo=timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)

        age_days = max(0, (current - posted).days)
        earned["freshness"] = (
            10 if age_days <= 7
            else 7 if age_days <= 30
            else 3 if age_days <= 60
            else 0
        )
    else:
        earned["freshness"] = 0
        unknown.append("freshness: verified posting date unavailable")

    # 6. Eligibility / compensation: 10 points
    # Split the ten points equally; unknown checks earn no points.
    earned["eligibility_compensation"] = 0

    if eligibility_match is None:
        unknown.append("eligibility: unknown")
    elif eligibility_match:
        earned["eligibility_compensation"] += 5

    if compensation_match is None:
        unknown.append("compensation: unknown")
    elif compensation_match:
        earned["eligibility_compensation"] += 5

    total = sum(earned.values())

    return {
        "rubric_version": RUBRIC_VERSION,
        "match_score": min(100, total),
        "score_breakdown": earned,
        "unknown_signals": unknown,
        "matched_skills": get_skill_gaps(job_skills, profile)[
            "matched_skills"
        ],
        "missing_skills": get_skill_gaps(job_skills, profile)[
            "missing_skills"
        ],
    }


def calculate_match_score(
    job_title: str,
    job_location: str,
    job_skills: list[str],
    profile: CandidateProfile,
) -> int:
    """Backward-compatible score function for existing API callers."""
    return calculate_match_breakdown(
        job_title=job_title,
        job_location=job_location,
        job_skills=job_skills,
        profile=profile,
    )["match_score"]


MY_PROFILE = CandidateProfile(
    target_roles=[
        "AI Engineer",
        "Machine Learning Engineer",
        "Generative AI Intern",
        "LLM Engineer",
        "Python Developer Intern",
        "RAG Engineer Intern",
        "AI Automation Engineer",
    ],
    skills=[
        "Python",
        "SQL",
        "Machine Learning",
        "FastAPI",
        "LangChain",
        "LangGraph",
        "Docker",
        "AWS",
        "RAG",
    ],
    preferred_locations=["Remote", "India"],
    projects=[],
    preferred_employment_types=["Internship", "Full-time"],
)
