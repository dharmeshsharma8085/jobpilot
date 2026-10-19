> [!WARNING]
> **🚧 Work in Progress — Under Active Development**
>
> JobPilot AI is currently under active development. Features, APIs, workflows, and the dashboard may be incomplete, untested, or subject to change. The project is **not production-ready** and is currently intended for development, testing, and experimentation only. Some features described in this README may not yet be fully implemented.


# 🚀 JobPilot AI

**An AI-powered job search and candidate-job matching platform.**

JobPilot AI is a personal AI job-search project designed to help candidates discover relevant job opportunities, compare job requirements with their skills, identify skill gaps, and manage their career preferences through a centralized platform.

The project is being developed incrementally, starting with a FastAPI backend and PostgreSQL database, followed by a Streamlit dashboard and future AI-powered job discovery and automation capabilities.

## ✨ Features

### 1. Backend API
- REST API built with FastAPI.
- Interactive API documentation using Swagger UI.
- Health-check endpoint to verify backend availability.
- Job creation and job-listing endpoints.
- Job search with filters for role, location, experience, employment type, skills, and minimum match score.

### 2. Candidate Profile Management
- Save and retrieve candidate preferences.
- Configure target job roles.
- Store technical skills and project experience.
- Set preferred locations and employment types.
- Persist profile data in PostgreSQL.

### 3. Job Matching Engine
- Calculate candidate-job match scores.
- Compare candidate skills with job requirements.
- Identify matched skills and missing skills.
- Generate a score breakdown and report unknown signals.
- Rank search results by match score.
- Maintain a versioned matching rubric.

### 4. Database and Migrations
- PostgreSQL database integration.
- SQLAlchemy ORM for database operations.
- Alembic for database schema migrations.
- Persistent storage for jobs and candidate profiles.

### 5. Dashboard — In Development
The planned Streamlit dashboard includes:

- **Dashboard:** Overview of stored jobs and candidate profile status.
- **Recommended Jobs:** Search and review jobs based on matching criteria.
- **Match Analysis:** Inspect match scores, matched skills, and skill gaps.
- **My Profile:** Update candidate preferences through a user interface.

> Dashboard implementation and runtime behavior should be verified locally before considering this module complete.

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Backend Framework | FastAPI |
| API Documentation | Swagger UI / OpenAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Database Migrations | Alembic |
| Data Validation | Pydantic |
| Dashboard | Streamlit |
| HTTP Client | Requests |
| Package Management | uv |
| Containerization | Docker Compose |
| Testing | pytest |
| Code Quality | Ruff |
| Version Control | Git and GitHub |

Additional AI and LLM libraries are included in the project dependencies for future integration.

## 📁 Project Structure

```text
jobpilot/
├── app/
│   ├── matching/
│   │   └── scorer.py
│   ├── models/
│   │   ├── job.py
│   │   └── profile_record.py
│   ├── profile/
│   │   ├── repository.py
│   │   └── schemas.py
│   ├── repositories/
│   │   └── job_repository.py
│   ├── services/
│   │   └── job_ingestion.py
│   ├── database.py
│   └── main.py
├── dashboard/
│   └── app.py
├── migrations/
├── scripts/
├── tests/
├── .env
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── uv.lock
└── README.md
```

*This structure reflects the modules created or referenced so far; confirm the actual files in your local repository before publishing.*

## ⚙️ Prerequisites

Install or configure the following:

- Python 3.14 or another Python version supported by the project configuration.
- uv package manager.
- Docker Desktop with Docker Compose.
- Git.
- A terminal and code editor such as VS Code.

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/dharmeshsharma8085/jobpilot.git
cd jobpilot
```

### 2. Install dependencies

```bash
uv sync
```

### 3. Configure environment variables

Create or update the `.env` file in the project root with the database connection settings required by the application.

Example format:

```dotenv
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/jobpilot
```

Replace the placeholders with your own database credentials. Never commit real credentials, API keys, or passwords to GitHub.

Verify that the database configuration used by the application and Alembic is consistent.

### 4. Start PostgreSQL

If PostgreSQL is configured through the project's Docker Compose file:

```bash
docker compose up -d
```

Verify that the database container is running:

```bash
docker compose ps
```

### 5. Apply database migrations

```bash
uv run alembic upgrade head
```

### 6. Start the FastAPI backend

```bash
uv run uvicorn app.main:app --reload --log-level debug
```

The backend should be available at:

- API base URL: http://127.0.0.1:8000
- Swagger documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

### 7. Start the Streamlit dashboard

Open a second terminal in the project root:

```bash
uv add requests
uv run streamlit run dashboard/app.py
```

The dashboard normally opens at:

http://localhost:8501

Keep the backend running while using the dashboard.

## 🔌 API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check backend health |
| GET | `/profile` | Retrieve the saved candidate profile |
| PUT | `/profile` | Create or update candidate preferences |
| POST | `/jobs` | Create a job record |
| GET | `/jobs` | Retrieve stored jobs |
| POST | `/jobs/search` | Search and rank jobs using matching criteria |

Use Swagger UI at `/docs` to inspect request schemas and test endpoints interactively.

### Example: Search Jobs

Request:

```json
{
  "role": "",
  "location": "",
  "experience": "",
  "job_type": "",
  "skills": [],
  "min_match_score": 0
}
```

The search endpoint returns matching jobs with their details, match scores, score breakdowns, matched skills, missing skills, and unknown signals.

The results depend on the jobs currently stored in the database.

## 🧪 Running Tests

Run the matching-engine tests:

```bash
uv run pytest tests/test_matching.py -q
```

Run the complete test suite:

```bash
uv run pytest -q
```

Check Python syntax:

```bash
uv run python -m compileall app
```

## 🔒 Security Considerations

- Keep `.env` and all secrets out of version control.
- Never expose database passwords or API keys in logs or API responses.
- Configure database credentials through environment variables.
- Review `alembic.ini` and other configuration files for hardcoded credentials.
- Use proper authentication and authorization before exposing the application publicly.
- Validate external job data before storing or processing it.
- Add appropriate logging, rate limiting, and error monitoring before production deployment.

## 🗺️ Development Roadmap

- [x] FastAPI backend foundation.
- [x] PostgreSQL integration and schema migrations.
- [x] Candidate profile storage and API endpoints.
- [x] Job listing and search API endpoints.
- [x] Initial candidate-job matching engine.
- [x] Match score breakdown and skill-gap reporting.
- [ ] Verify the full automated test suite.
- [ ] Complete and validate the Streamlit dashboard.
- [ ] Integrate real job sources and automated job ingestion.
- [ ] Integrate an LLM for useful job-search assistance.
- [ ] Build agentic workflows for job discovery and application preparation.
- [ ] Add scheduled automation and notifications.
- [ ] Add production security, deployment, and monitoring.

## 🎯 Project Goal

The long-term goal of JobPilot AI is to evolve into a personalized job-search assistant that can discover relevant opportunities, evaluate job-candidate compatibility, explain skill gaps, and automate parts of the job-search workflow while keeping users in control of important actions.

## 👨‍💻 Author

**Dharmesh Sharma**

B.Tech — Artificial Intelligence

GitHub: [@dharmeshsharma8085](https://github.com/dharmeshsharma8085)

---

*JobPilot AI is an actively developing project. Features listed as planned or in development may not yet be fully implemented or production-ready.*
