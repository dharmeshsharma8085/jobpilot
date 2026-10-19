
import os

import requests
import streamlit as st

st.set_page_config(
    page_title="JobPilot AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = os.getenv("JOBPILOT_API_URL", "http://127.0.0.1:8000")

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    .job-card {
        border: 1px solid #e4e7ec;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 14px;
        background: var(--secondary-background-color);
    }
    .muted {color: #667085; font-size: 0.9rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def api_request(method, path, **kwargs):
    try:
        response = requests.request(
            method,
            f"{API_BASE_URL}{path}",
            timeout=15,
            **kwargs,
        )
        if response.ok:
            return response.json()

        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text

        st.error(f"API error ({response.status_code}): {detail}")
    except requests.RequestException as exc:
        st.error(
            "Backend se connection nahi ho paaya. "
            "Check karo ki FastAPI server chal raha hai."
        )
        st.caption(str(exc))

    return None


def show_skills(skills, empty_message="No skills listed"):
    if not skills:
        st.caption(empty_message)
        return

    st.write(" · ".join(str(skill) for skill in skills))


st.sidebar.title("🚀 JobPilot AI")
st.sidebar.caption("Your AI-powered job search companion")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Recommended Jobs", "My Profile"],
)

health = api_request("GET", "/health")

if health:
    st.sidebar.success("Backend connected")
else:
    st.sidebar.warning("Backend connection unavailable")


if page == "Dashboard":
    st.title("Welcome to JobPilot AI")
    st.write(
        "Find relevant opportunities, understand your skill gaps, "
        "and manage your candidate profile."
    )

    jobs = api_request("GET", "/jobs?limit=100")
    profile = api_request("GET", "/profile")

    if jobs is not None:
        total_jobs = len(jobs)
        scored_jobs = [
            job for job in jobs if job.get("match_score") is not None
        ]
        average_score = (
            sum(job["match_score"] for job in scored_jobs) / len(scored_jobs)
            if scored_jobs
            else 0
        )

        col1, col2, col3 = st.columns(3)
        col1.metric("Jobs in Database", total_jobs)
        col2.metric(
            "Average Stored Match Score",
            f"{average_score:.1f}%" if scored_jobs else "Not calculated",
        )
        col3.metric(
            "Profile",
            "Saved" if profile else "Not available",
        )

        st.subheader("Recently Added Jobs")

        if jobs:
            for job in jobs[:5]:
                with st.container(border=True):
                    st.markdown(f"**{job.get('title', 'Untitled role')}**")
                    st.caption(
                        f"{job.get('company', 'Unknown company')} · "
                        f"{job.get('location', 'Location not specified')}"
                    )
                    if job.get("job_url"):
                        st.markdown(
                            f"[View opportunity]({job['job_url']})"
                        )
        else:
            st.info(
                "Database mein abhi koi job nahi hai. "
                "Pehle job records add karo."
            )

    if profile:
        st.subheader("Your Target Roles")
        show_skills(profile.get("target_roles", []))


elif page == "Recommended Jobs":
    st.title("Recommended Jobs")
    st.write("Search jobs and inspect your match scores and skill gaps.")

    with st.form("job_search_form"):
        col1, col2 = st.columns(2)

        role = col1.text_input("Target role", placeholder="AI Engineer")
        location = col2.text_input(
            "Location",
            placeholder="Remote or India",
        )

        col3, col4 = st.columns(2)

        job_type = col3.selectbox(
            "Employment type",
            ["Any", "Internship", "Full-time", "Part-time", "Contract"],
        )
        experience = col4.text_input(
            "Experience keyword",
            placeholder="Entry level",
        )

        skills_text = st.text_input(
            "Required skills (comma-separated)",
            placeholder="Python, SQL, LangChain",
        )
        min_score = st.slider("Minimum match score", 0, 100, 0)

        submitted = st.form_submit_button(
            "Find Matching Jobs",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        skills = [
            item.strip()
            for item in skills_text.split(",")
            if item.strip()
        ]

        payload = {
            "role": role.strip(),
            "location": location.strip(),
            "experience": experience.strip(),
            "job_type": "" if job_type == "Any" else job_type,
            "skills": skills,
            "min_match_score": min_score,
        }

        result = api_request("POST", "/jobs/search", json=payload)

        if result is not None:
            st.session_state["jobpilot_search_results"] = result

    result = st.session_state.get("jobpilot_search_results")

    if result is not None:
        st.subheader(f"Found {result.get('count', 0)} matching jobs")

        for job in result.get("jobs", []):
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(f"### {job.get('title', 'Untitled role')}")
                    st.write(
                        f"**{job.get('company', 'Unknown company')}** · "
                        f"{job.get('location', 'Location not specified')}"
                    )
                    st.caption(
                        f"Source: {job.get('source', 'Unknown')} · "
                        f"Type: {job.get('employment_type', 'Not specified')}"
                    )

                with col2:
                    score = job.get("match_score", 0)
                    st.metric("Match score", f"{score}%")

                with st.expander("View match analysis"):
                    left, right = st.columns(2)

                    with left:
                        st.markdown("**Matched skills**")
                        show_skills(
                            job.get("matched_skills", []),
                            "No matched skills reported",
                        )

                    with right:
                        st.markdown("**Skills to develop**")
                        show_skills(
                            job.get("missing_skills", []),
                            "No missing skills reported",
                        )

                    st.markdown("**Score breakdown**")
                    breakdown = job.get("score_breakdown", {})

                    if breakdown:
                        for category, value in breakdown.items():
                            if isinstance(value, (int, float)):
                                st.write(f"{category.replace('_', ' ').title()}: {value}")
                                st.progress(max(0.0, min(1.0, float(value) / 100)))
                            else:
                                st.write(f"{category}: {value}")
                    else:
                        st.caption("No score breakdown available.")

                    unknown = job.get("unknown_signals", [])
                    if unknown:
                        st.caption(f"Unknown signals: {unknown}")

                if job.get("job_url"):
                    st.link_button(
                        "View / Apply",
                        job["job_url"],
                        use_container_width=False,
                    )

        if not result.get("jobs"):
            st.info(
                "Koi matching job nahi mili. Filters kam karke dobara try karo."
            )

    else:
        st.info("Filters select karke Find Matching Jobs par click karo.")


elif page == "My Profile":
    st.title("My Candidate Profile")
    st.write("Apni preferences update karo; changes backend database mein save honge.")

    profile = api_request("GET", "/profile")

    if profile:
        with st.form("profile_form"):
            target_roles = st.text_area(
                "Target roles (one per line)",
                value="\n".join(profile.get("target_roles", [])),
            )
            skills = st.text_area(
                "Skills (one per line)",
                value="\n".join(profile.get("skills", [])),
            )
            locations = st.text_area(
                "Preferred locations (one per line)",
                value="\n".join(profile.get("preferred_locations", [])),
            )
            projects = st.text_area(
                "Projects (one per line)",
                value="\n".join(profile.get("projects", [])),
            )
            employment_types = st.text_area(
                "Preferred employment types (one per line)",
                value="\n".join(
                    profile.get("preferred_employment_types", [])
                ),
            )

            save = st.form_submit_button(
                "Save Profile",
                type="primary",
            )

        if save:
            payload = {
                "target_roles": [
                    item.strip()
                    for item in target_roles.splitlines()
                    if item.strip()
                ],
                "skills": [
                    item.strip()
                    for item in skills.splitlines()
                    if item.strip()
                ],
                "preferred_locations": [
                    item.strip()
                    for item in locations.splitlines()
                    if item.strip()
                ],
                "projects": [
                    item.strip()
                    for item in projects.splitlines()
                    if item.strip()
                ],
                "preferred_employment_types": [
                    item.strip()
                    for item in employment_types.splitlines()
                    if item.strip()
                ],
            }

            updated = api_request("PUT", "/profile", json=payload)

            if updated is not None:
                st.success("Profile saved successfully!")
                st.rerun()

    else:
        st.warning(
            "Profile load nahi hui. Backend check karo aur profile endpoint "
            "verify karo."
        )
