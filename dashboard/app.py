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
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_request(method, path, **kwargs):
    """Call the JobPilot FastAPI backend and show useful errors."""
    try:
        response = requests.request(
            method,
            f"{API_BASE_URL}{path}",
            timeout=15,
            **kwargs,
        )

        if response.ok:
            if response.status_code == 204:
                return {}
            try:
                return response.json()
            except ValueError:
                return {}

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


def format_label(value):
    return str(value).replace("_", " ").replace("-", " ").title()


def show_job_details(job):
    """Render a selected job's detail and match-analysis view."""
    st.title(job.get("title", "Job Details"))
    st.subheader(job.get("company", "Unknown company"))

    col1, col2, col3 = st.columns(3)
    col1.metric("Match score", f"{job.get('match_score', 0)}%")
    col2.write("**Location**")
    col2.write(job.get("location") or "Not specified")
    col3.write("**Employment type**")
    col3.write(job.get("employment_type") or "Not specified")

    st.caption(
        f"Source: {job.get('source', 'Unknown')} · "
        f"Rubric version: {job.get('rubric_version', 'Not available')}"
    )

    if job.get("job_url"):
        st.link_button(
            "Open Original Job / Apply",
            job["job_url"],
            type="primary",
        )

    st.divider()
    st.subheader("Required Skills")
    show_skills(job.get("required_skills", []), "No required skills listed.")

    left, right = st.columns(2)
    with left:
        st.markdown("**Matched skills**")
        show_skills(
            job.get("matched_skills", []),
            "No matched skills reported.",
        )
    with right:
        st.markdown("**Skills to develop**")
        show_skills(
            job.get("missing_skills", []),
            "No missing skills reported.",
        )

    st.subheader("Match Score Breakdown")
    breakdown = job.get("score_breakdown") or {}
    if breakdown:
        for category, value in breakdown.items():
            st.write(f"**{format_label(category)}:** {value}")
            if isinstance(value, (int, float)):
                st.progress(max(0.0, min(1.0, float(value) / 100)))
    else:
        st.caption("No score breakdown available.")

    unknown = job.get("unknown_signals", [])
    if unknown:
        st.info(f"Signals not available for scoring: {', '.join(map(str, unknown))}")

    if st.button("← Back to Recommended Jobs"):
        st.session_state["jobpilot_page"] = "Recommended Jobs"
        st.rerun()


st.sidebar.title("🚀 JobPilot AI")
st.sidebar.caption("Your AI-powered job search companion")

# A selection made by a button takes priority for the next rerun.
default_page = st.session_state.pop("jobpilot_page", "Dashboard")
page_options = ["Dashboard", "Recommended Jobs", "Job Details", "My Profile"]
if default_page not in page_options:
    default_page = "Dashboard"

page = st.sidebar.radio(
    "Navigation",
    page_options,
    index=page_options.index(default_page),
    key="jobpilot_navigation",
)

health = api_request("GET", "/health")
if health:
    st.sidebar.success("Backend connected")
else:
    st.sidebar.warning("Backend connection unavailable")


# -------------------------
# Dashboard
# -------------------------
if page == "Dashboard":
    st.title("Welcome to JobPilot AI")
    st.write(
        "Find relevant opportunities, understand your skill gaps, "
        "and manage your career preferences."
    )

    jobs = api_request("GET", "/jobs?limit=100")
    profile = api_request("GET", "/profile")

    if jobs is not None:
        total_jobs = len(jobs)
        scored_jobs = [
            job for job in jobs
            if job.get("match_score") is not None
        ]
        average_score = (
            sum(job["match_score"] for job in scored_jobs) / len(scored_jobs)
            if scored_jobs else None
        )

        col1, col2, col3 = st.columns(3)
        col1.metric("Jobs in Database", total_jobs)
        col2.metric(
            "Average Stored Match Score",
            f"{average_score:.1f}%" if average_score is not None else "Not calculated",
        )
        col3.metric("Profile", "Saved" if profile else "Not available")

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
                        st.link_button("View opportunity", job["job_url"])
        else:
            st.info("Database mein abhi koi job nahi hai. Pehle job records add karo.")

    if profile:
        st.subheader("Your Target Roles")
        show_skills(profile.get("target_roles", []))


# -------------------------
# Recommended Jobs
# -------------------------
elif page == "Recommended Jobs":
    st.title("Recommended Jobs")
    st.write("Search jobs and inspect your match scores and skill gaps.")

    with st.form("job_search_form"):
        col1, col2 = st.columns(2)
        role = col1.text_input("Target role", placeholder="AI Engineer")
        location = col2.text_input("Location", placeholder="Remote or India")

        col3, col4 = st.columns(2)
        job_type = col3.selectbox(
            "Employment type",
            ["Any", "Internship", "Full-time", "Part-time", "Contract"],
        )
        experience = col4.text_input("Experience keyword", placeholder="Entry level")
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
        skills = [item.strip() for item in skills_text.split(",") if item.strip()]
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
                    st.metric("Match score", f"{job.get('match_score', 0)}%")

                button_col, apply_col = st.columns([1, 1])
                with button_col:
                    if st.button(
                        "View Details",
                        key=f"job_details_{job.get('id', job.get('job_url', job.get('title')))}",
                        use_container_width=True,
                    ):
                        st.session_state["selected_job"] = job
                        st.session_state["jobpilot_page"] = "Job Details"
                        st.rerun()
                with apply_col:
                    if job.get("job_url"):
                        st.link_button(
                            "View / Apply",
                            job["job_url"],
                            use_container_width=True,
                        )

                with st.expander("Quick match analysis"):
                    left, right = st.columns(2)
                    with left:
                        st.markdown("**Matched skills**")
                        show_skills(job.get("matched_skills", []), "No matched skills reported")
                    with right:
                        st.markdown("**Skills to develop**")
                        show_skills(job.get("missing_skills", []), "No missing skills reported")

                    st.markdown("**Score breakdown**")
                    breakdown = job.get("score_breakdown") or {}
                    if breakdown:
                        for category, value in breakdown.items():
                            label = format_label(category)
                            st.write(f"{label}: {value}")
                            if isinstance(value, (int, float)):
                                st.progress(max(0.0, min(1.0, float(value) / 100)))
                    else:
                        st.caption("No score breakdown available.")

                    unknown = job.get("unknown_signals", [])
                    if unknown:
                        st.caption(f"Signals not available: {', '.join(map(str, unknown))}")

        if not result.get("jobs"):
            st.info("Koi matching job nahi mili. Filters kam karke dobara try karo.")
    else:
        st.info("Filters select karke Find Matching Jobs par click karo.")


# -------------------------
# Job Details
# -------------------------
elif page == "Job Details":
    selected_job = st.session_state.get("selected_job")
    if selected_job:
        show_job_details(selected_job)
    else:
        st.title("Job Details")
        st.info("Pehle Recommended Jobs page par jaakar kisi job ka View Details button click karo.")
        if st.button("Go to Recommended Jobs"):
            st.session_state["jobpilot_page"] = "Recommended Jobs"
            st.rerun()


# -------------------------
# My Profile
# -------------------------
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
                value="\n".join(profile.get("preferred_employment_types", [])),
            )
            save = st.form_submit_button("Save Profile", type="primary")

        if save:
            payload = {
                "target_roles": [item.strip() for item in target_roles.splitlines() if item.strip()],
                "skills": [item.strip() for item in skills.splitlines() if item.strip()],
                "preferred_locations": [item.strip() for item in locations.splitlines() if item.strip()],
                "projects": [item.strip() for item in projects.splitlines() if item.strip()],
                "preferred_employment_types": [
                    item.strip() for item in employment_types.splitlines() if item.strip()
                ],
            }
            updated = api_request("PUT", "/profile", json=payload)
            if updated is not None:
                st.success("Profile saved successfully!")
                st.rerun()
    else:
        st.warning(
            "Profile load nahi hui. Backend check karo aur profile endpoint verify karo."
        )
