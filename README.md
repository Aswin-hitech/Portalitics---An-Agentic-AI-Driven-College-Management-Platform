# ⚡ Portalitics — Agentic AI-Driven College Management Platform

**Portalitics** is a proactive academic intervention system, not an analytics dashboard with an LLM bolted on. It detects what is changing in a student's academic record, explains *why* using verified metrics, recommends what should happen next, routes that recommendation to the right person, and tracks whether the intervention actually worked — all through a minimal, auditable set of LangChain agents running on Groq's low-latency inference.

> Built for the "Agentic AI" evaluation track — Code Quality, Architecture, Security, and Innovation.

---

## Table of Contents

- [Why Portalitics Is Different](#why-portalitics-is-different)
- [Agentic AI Architecture](#agentic-ai-architecture)
- [Feature Overview](#feature-overview)
- [Tech Stack](#tech-stack)
- [Folder Structure](#folder-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Demo Credentials](#demo-credentials)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Security Notes](#security-notes)
- [Known Issues & Roadmap](#known-issues--roadmap)
- [License](#license)

---

## Why Portalitics Is Different

A common weakness of student-analytics-plus-LLM systems is that they're insight-oriented, not action-oriented — they tell you "Ram is at risk" and stop there. Portalitics is built around five strategies that make the AI layer a real product feature rather than a decorative one:

| # | Strategy | What it means |
|---|---|---|
| 1 | **Proactive Intervention** | The system answers *why* a student is at risk and *what should happen next*, not just that they are — producing an intervention, not an alert. |
| 2 | **Multi-Signal Risk Intelligence** | Risk is computed from attendance trend, grade trend, assignment completion, and submission delays together, never a single threshold in isolation. |
| 3 | **Evidence-Grounded AI** | Every recommendation follows Observation → Evidence → Recommendation, traceable back to the exact metrics that produced it. |
| 4 | **Closed-Loop Intervention** | Once a faculty member acts on a recommendation, the system tracks the student's metrics over a 14-day window and reports whether it worked. |
| 5 | **Human-in-the-Loop** | AI detects, scores, and recommends. Faculty and admins make the final call — the system never auto-executes an intervention. |

---

## Agentic AI Architecture

The AI layer is deliberately minimal: **one orchestrator + three specialist agents**, each owning a distinct decision, coordinated with real LangChain tool-calling and LCEL chains (not a single monolithic "AI engine").

```
Dashboard / Faculty Action / Cron Trigger
        │
        ▼
  Orchestrator (LangChain Router — app/agents/orchestrator.py)
        │
        ├──► Performance Analysis Agent   "What changed?"
        │        (attendance %, grade trend, assignment completion)
        │
        ├──► Risk & Recommendation Agent  "What does it mean, and what next?"
        │        (deterministic rules engine + Groq LLM reasoning)
        │
        └──► Report & Insight Agent       "How should this be communicated?"
                 (role-specific summary: student / faculty / admin)
```

| Agent | File | Decision it owns |
|---|---|---|
| Orchestrator | `app/agents/orchestrator.py` | Which agents run, in what sequence, via LangChain `@tool` bindings + `RunnableLambda` LCEL chain |
| Performance Analysis Agent | `app/agents/performance_agent.py` | Computes attendance, grades, and assignment metrics from MongoDB |
| Risk & Recommendation Agent | `app/agents/risk_agent.py` | Multi-signal composite risk score + evidence-grounded recommendation |
| Report & Insight Agent | `app/agents/report_agent.py` | Formats output for the requesting role (student / faculty / admin) |

**Anti-hallucination design:** the LLM never invents facts about a student. Thresholds and the composite risk score are computed deterministically in `app/services/rules_engine.py`; Groq (via `langchain-groq`) only reasons over already-verified, structured metrics and phrases the recommendation.

```
Attendance = 72%, Grades: 78→64→55, Assignments: 68%
        │
        ▼
  Python Rules Engine (deterministic thresholds + weighting)
        │
        ▼
  Structured risk object (JSON)
        │
        ▼
  Groq LLM — reasoning + natural-language phrasing only
        │
        ▼
  Evidence-grounded recommendation → Faculty
```

Every orchestrator call writes an audit row to the `agent_logs` collection for traceability.

---

## Feature Overview

**Public**
- Home, course catalog with search/filter, course details, departments, events, notices, contact form.

**Student**
- Dashboard, courses, timetable, attendance, grades, assignments (with real file/text submission), "My Progress" with evidence-grounded AI insights, profile.

**Faculty**
- Dashboard, class & student management, attendance marking, assignment creation, exam/marks entry, AI-generated feedback assist, priority intervention queue (Critical / Needs Attention / Monitor), intervention detail view with initiate/update-status actions, profile.

**HOD (Head of Department)**
- Department-level dashboard with aggregated faculty/class insights and AI assist.

**Admin**
- Manage students, teachers, courses, classes, exams, assignments; institution-wide analytics, live intervention-outcome tracking, system monitoring, comparative & institutional PDF reports (via ReportLab).

**AI Assist**
- Natural-language command bar (`/api/ai-assist`) for faculty/admin — e.g. "update Aswin's OOPS mark to 92" — parsed via regex fallback with fuzzy student-name matching, sanitized against NoSQL injection.

---

## Tech Stack

Python, FastAPI, Uvicorn, Jinja2, HTML5, CSS3, JavaScript, LangChain, Groq LLM, MongoDB, PyMongo, Motor, mongomock, Pydantic, python-dotenv, PyJWT, Passlib (bcrypt), Chart.js, Lucide Icons, ReportLab, pytest, httpx

---

## Folder Structure

```
Portalitics/
├── app/
│   ├── main.py                    # FastAPI entrypoint, middleware & router registration
│   ├── agents/
│   │   ├── orchestrator.py        # LangChain router — LCEL chain over the 3 agents below
│   │   ├── performance_agent.py   # Agent 1 — performance metrics
│   │   ├── risk_agent.py          # Agent 2 — risk scoring + recommendations
│   │   └── report_agent.py        # Agent 3 — role-formatted reports
│   ├── api/
│   │   ├── public.py              # Home, courses, departments, events, notices, contact
│   │   ├── auth.py                # Login, register, logout, rate-limited auth
│   │   ├── student.py             # Student dashboard, assignments, progress
│   │   ├── faculty.py             # Attendance, assignments, exams, intervention queue
│   │   ├── admin.py                # Manage students/teachers/courses, analytics
│   │   ├── interventions.py       # Initiate & update intervention status
│   │   ├── reports.py             # PDF report generation (ReportLab)
│   │   └── ai_assist.py           # Natural-language AI command endpoint
│   ├── services/
│   │   ├── mongo_client.py        # MongoDB connection, auto-seed fallback to mongomock
│   │   ├── groq_client.py         # Groq LLM client via langchain-groq
│   │   ├── rules_engine.py        # Deterministic thresholds & composite risk scoring
│   │   ├── intervention_service.py# Intervention lifecycle & outcome calculation
│   │   └── ai_assist_agent.py     # NL command parsing, fuzzy student search
│   ├── core/
│   │   ├── config.py              # Pydantic Settings, validates APP_SECRET_KEY at startup
│   │   ├── security.py            # Password hashing, JWT, current-user resolution
│   │   ├── csrf.py                # CSRF middleware
│   │   ├── logging.py             # Structured app logger
│   │   └── templates.py           # Jinja2Templates + global context processor
│   └── templates/                 # Jinja2 HTML (public/, student/, faculty/, admin/, reports/)
├── static/
│   ├── css/                       # base.css, dashboard.css, navbar.css
│   └── js/                        # main.js, charts.js, interventions.js
├── scripts/
│   ├── seed_database.py           # Seeds demo users, courses, attendance, grades
│   ├── generate_demo_data.py
│   └── reset_demo_data.py
├── tests/
│   ├── conftest.py
│   ├── test_agents.py
│   ├── test_api.py
│   └── test_risk_engine.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- A running MongoDB instance (optional — falls back to an in-memory `mongomock` store with an auto-seeded demo dataset if unreachable, with a loud console warning that data won't persist)
- A [Groq API key](https://console.groq.com) for LLM-backed recommendations

### Installation

```bash
# 1. Clone the repository and enter it
cd portalitics

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# then edit .env — at minimum set APP_SECRET_KEY and GROQ_API_KEY
# (the app will refuse to start if APP_SECRET_KEY is missing or left as the placeholder)

# 5. Seed the database (optional if using mongomock auto-seed)
python scripts/seed_database.py

# 6. Run the server
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000** in your browser.

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `APP_NAME` | Application name | `Portalitics` |
| `APP_ENV` | `development` / `testing` / `production` | `development` |
| `APP_SECRET_KEY` | JWT signing secret — **required**, app fails fast if left as placeholder | *(none — must be set)* |
| `APP_PORT` | Server port | `8000` |
| `DEMO_MODE` | Flags the app as running on demo/ephemeral data | `False` |
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `MONGODB_DB_NAME` | Database name | `portalitics_db` |
| `GROQ_API_KEY` | Groq API key for LLM inference | *(none)* |
| `GROQ_MODEL` | Groq model identifier | `llama-3.3-70b-versatile` |
| `AT_RISK_ATTENDANCE_THRESHOLD` | Attendance % floor before flagging | `75.0` |
| `AT_RISK_GRADE_DROP_PERCENT` | Grade-drop % that contributes to risk | `15.0` |
| `RISK_WEIGHT_ATTENDANCE` | Composite risk weighting | `0.3` |
| `RISK_WEIGHT_GRADES` | Composite risk weighting | `0.3` |
| `RISK_WEIGHT_ASSIGNMENTS` | Composite risk weighting | `0.2` |
| `RISK_WEIGHT_SUBMISSION_DELAYS` | Composite risk weighting | `0.2` |
| `AT_RISK_SUPPORT_THRESHOLD` | Composite score → "Support Recommended" tier | `30.0` |
| `AT_RISK_IMMEDIATE_THRESHOLD` | Composite score → "Immediate Attention Needed" tier | `55.0` |
| `INTERVENTION_EVALUATION_WINDOW_DAYS` | Days before an intervention outcome is evaluated | `14` |

---

## Demo Credentials

After running `scripts/seed_database.py`, all seeded accounts share the password below:

| Role | Email pattern | Password |
|---|---|---|
| Admin | `admin@college.edu` | `password123` |
| HOD | `hod.cs@college.edu`, `hod.math@college.edu` | `password123` |
| Faculty | `faculty1@college.edu`, `faculty2@college.edu`, ... | `password123` |
| Student | `student1@college.edu`, `student2@college.edu`, ... | `password123` |

> Change these before any non-local deployment.

---

## API Reference

All routes are server-rendered (`HTMLResponse`) unless noted as JSON.

**Public** — `/`, `/explore`, `/courses`, `/courses/{course_id}`, `/departments`, `/events`, `/notices`, `/contact` (GET/POST)

**Auth** — `/login` (GET/POST), `/register` (GET/POST), `/admin/login`, `/logout`

**Student** (`/student/*`) — `/dashboard`, `/profile`, `/profile/update-avatar` (POST), `/courses`, `/timetable`, `/attendance`, `/grades`, `/progress`, `/assignments`, `/assignments/submit` (POST), `/api/charts` (JSON)

**Faculty** (`/faculty/*`) — `/dashboard`, `/hod-dashboard`, `/classes`, `/students`, `/attendance`, `/attendance/mark` (POST), `/assignments`, `/assignments/create` (POST), `/exams`, `/exams/record` (POST), `/intervention_queue`, `/intervention_details/{id}`, `/api/charts` (JSON), `/profile`, `/profile/update-avatar` (POST)

**Admin** (`/admin/*`) — `/dashboard`, `/students`, `/users/add` (POST), `/teachers`, `/classes`, `/courses`, `/exams`, `/assignments`, `/intervention_outcomes`, `/analytics`, `/system_monitoring`, `/api/charts/dashboard` (JSON), `/profile`, `/profile/update-avatar` (POST)

**Interventions** (`/api/interventions/*`) — `/initiate` (POST), `/update_status` (POST)

**Reports** (`/reports/*`) — `/student/{student_id}` (PDF), `/institution` (PDF), `/class/{class_id}`, `/comparative`

**AI Assist** — `/api/ai-assist` (POST, JSON) — natural-language command endpoint for faculty/admin

---

## Testing

```bash
pytest
```

Covers agent output shape (`test_agents.py`), the composite risk-scoring engine (`test_risk_engine.py`), and core API routes (`test_api.py`). Coverage currently spans a subset of the full route surface — contributions expanding coverage to every endpoint and to negative-path cases (missing student, Groq API failure, empty history) are welcome.

---

## Security Notes

- Passwords are hashed with **bcrypt** via `passlib`; sessions use **httponly, samesite=lax** JWT cookies.
- `APP_SECRET_KEY` is validated at startup — the app refuses to boot on a missing or placeholder key outside `APP_ENV=testing`.
- Login is protected by an in-memory sliding-window **rate limiter** (5 attempts / 60s per IP).
- **CSRF protection** is enforced on all `POST`/`PUT`/`DELETE` requests via a custom middleware (`app/core/csrf.py`) cross-referencing a hidden form token against an httponly cookie.
- Faculty/admin AI-assist free-text input is sanitized before use in MongoDB `$regex` queries to prevent NoSQL injection.
- The mongomock in-memory fallback prints an explicit, boxed console warning when active, since data will not persist across restarts.

---

## Known Issues & Roadmap

Documented openly for evaluators and contributors:

- **Intervention status update parameter mismatch** — `POST /api/interventions/update_status` expects a form field named `margin_id`, but `templates/faculty/intervention_details.html` submits `intervention_id`. This currently breaks the "mark intervention started/resolved" action. **Fix:** rename the field in either the route or the template so they match (a legacy-named route, `update_status_legacy`, already accepts the old field name as a stopgap).
- **CSRF token can render empty on a session's very first page load** if that page is reached directly (e.g., a bookmark straight to `/login`) before any other page has set the cookie, causing the first submission to fail with 403 until refreshed. **Fix:** generate and set the CSRF cookie earlier in the middleware's request lifecycle, before the response is rendered.
- **Public navbar has no working mobile menu** — `#mobileMenuBtn` is permanently hidden with no JS handler, and `.nav-links` has no responsive breakpoint in `navbar.css`. The authenticated dashboard sidebar already collapses correctly on mobile; the public nav needs the same treatment.
- **No loading/error UI states** around `fetch()` calls in `charts.js` or the inline AI-assist calls in dashboard templates.
- **No empty states** for the intervention queue, dashboards, or assignment lists when there is no data to show.
- **Test coverage** should be expanded beyond the current subset to cover all API routes and negative paths.

---

## License

Add your license of choice (MIT recommended for hackathon submissions) before publishing.
