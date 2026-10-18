
from datetime import datetime, timezone

from app.matching.scorer import (
    CandidateProfile,
    calculate_match_breakdown,
    calculate_match_score,
    get_skill_gaps,
)


def test_score_does_not_award_points_for_unknown_signals():
    profile = CandidateProfile(
        target_roles=["AI Engineer"],
        skills=["Python", "FastAPI"],
        preferred_locations=["Remote"],
    )

    result = calculate_match_breakdown(
        job_title="AI Engineer Intern",
        job_location="Remote",
        job_skills=["Python", "FastAPI"],
        profile=profile,
    )

    assert result["score_breakdown"]["skills"] == 35
    assert result["score_breakdown"]["role_level"] == 15
    assert result["score_breakdown"]["location_work_mode"] == 10
    assert result["match_score"] == 60
    assert result["unknown_signals"]


def test_no_role_skill_or_location_match_scores_zero():
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


def test_skill_aliases_are_matched():
    profile = CandidateProfile(
        target_roles=["LLM Engineer"],
        skills=["LLMs", "Fast API"],
        preferred_locations=["Remote"],
    )

    result = get_skill_gaps(
        ["Large Language Models", "FastAPI", "Docker"],
        profile,
    )

    assert result["matched_skills"] == [
        "Large Language Models",
        "FastAPI",
    ]
    assert result["missing_skills"] == ["Docker"]


def test_fresh_posting_receives_full_freshness_points():
    profile = CandidateProfile(
        target_roles=["AI Engineer"],
        skills=["Python"],
        preferred_locations=["Remote"],
    )

    result = calculate_match_breakdown(
        job_title="AI Engineer Intern",
        job_location="Remote",
        job_skills=["Python"],
        profile=profile,
        posted_at=datetime(2026, 10, 17, tzinfo=timezone.utc),
        now=datetime(2026, 10, 18, tzinfo=timezone.utc),
        eligibility_match=True,
        compensation_match=True,
    )

    assert result["score_breakdown"]["freshness"] == 10
    assert result["score_breakdown"]["eligibility_compensation"] == 10


def test_unknown_location_is_not_a_match():
    profile = CandidateProfile(
        target_roles=["AI Engineer"],
        skills=["Python"],
        preferred_locations=["Remote"],
    )

    result = calculate_match_breakdown(
        job_title="AI Engineer Intern",
        job_location="Not specified",
        job_skills=["Python"],
        profile=profile,
    )

    assert result["score_breakdown"]["location_work_mode"] == 0
    assert any("location unavailable" in item
               for item in result["unknown_signals"])
