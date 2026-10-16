
from app.matching.scorer import (
    CandidateProfile,
    calculate_match_score,
)


def test_perfect_match_scores_100():
    profile = CandidateProfile(
        target_roles=["AI Engineer"],
        skills=["Python", "FastAPI"],
        preferred_locations=["Remote"],
    )

    score = calculate_match_score(
        job_title="AI Engineer Intern",
        job_location="Remote",
        job_skills=["Python", "FastAPI"],
        profile=profile,
    )

    assert score == 100


def test_no_match_scores_zero():
    profile = CandidateProfile(
        target_roles=["AI Engineer"],
        skills=["Python", "FastAPI"],
        preferred_locations=["Remote"],
    )

    score = calculate_match_score(
        job_title="Graphic Designer",
        job_location="On-site London",
        job_skills=["Photoshop", "Illustrator"],
        profile=profile,
    )

    assert score == 0


def test_partial_skill_match():
    profile = CandidateProfile(
        target_roles=["AI Engineer"],
        skills=["Python", "FastAPI"],
        preferred_locations=["Remote"],
    )

    score = calculate_match_score(
        job_title="AI Engineer Intern",
        job_location="Remote",
        job_skills=["Python", "Docker"],
        profile=profile,
    )

    assert score == 65
