
from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateProfile:
    target_roles: list[str]
    skills: list[str]
    preferred_locations: list[str]


def calculate_match_score(
    job_title: str,
    job_location: str,
    job_skills: list[str],
    profile: CandidateProfile,
) -> int:
    """Return a transparent 0-100 job relevance score."""

    title = job_title.casefold()
    location = job_location.casefold()

    role_match = any(
        role.casefold() in title
        for role in profile.target_roles
    )

    candidate_skills = {skill.casefold() for skill in profile.skills}
    required_skills = {skill.casefold() for skill in job_skills}

    skill_score = (
        len(candidate_skills & required_skills) / len(required_skills) * 70
        if required_skills
        else 0
    )

    location_match = any(
        preferred.casefold() in location
        for preferred in profile.preferred_locations
    )

    role_score = 20 if role_match else 0
    location_score = 10 if location_match else 0

    return round(min(100, role_score + skill_score + location_score))


MY_PROFILE = CandidateProfile(
    target_roles=[
        "AI Engineer",
        "Machine Learning Engineer",
        "Generative AI Intern",
        "LLM Engineer",
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
    ],
    preferred_locations=["Remote", "India"],
)
