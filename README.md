# ⚡ Portalitics — Agentic AI Academic Management Platform

**Portalitics** is a deployable Agentic AI-Driven Student Success & Proactive Academic Support System. It combines deterministic Python rules with LangChain multi-agent orchestration and Groq LLM reasoning to detect learning friction, initiate faculty care plans, and track 14-day growth outcomes.

---

## 🎨 Design System
- **Theme Palette**: White to Dark-Red (`#7A0C0C`) to Light-Red (`#FFECEC`) Gradient Theme.
- **Language**: Designed with student and faculty friendly non-technical language (*"Student Learning Support Queue"*, *"Immediate Attention Needed"*, *"14-Day Growth Tracking"*).

---

## 🤖 Multi-Agent Architecture
1. **Performance Analysis Agent** (`app/agents/performance_agent.py`): Computes attendance trends, grade drops, and coursework completion directly from MongoDB.
2. **Risk & Recommendation Agent** (`app/agents/risk_agent.py`): Combines deterministic Python rules (Anti-hallucination layer) with Groq LLM reasoning.
3. **Report & Insight Agent** (`app/agents/report_agent.py`): Formats actionable summaries for Students, Faculty, and Administrators.
4. **Agent Orchestrator** (`app/agents/orchestrator.py`): Central LangChain event router.

---

## 🗄️ Database Architecture
- **MongoDB Collection (`portalitics_db`)**: Single source of truth for Users, Courses, Classes, Attendance logs, Coursework submissions, Exam scores, Interventions, and Agent audit logs.

---

## 🚀 Quick Start Instructions

```bash
# 1. Clone repository & set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed MongoDB database
python scripts/seed_database.py

# 4. Start ASGI server
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000` in your web browser.
