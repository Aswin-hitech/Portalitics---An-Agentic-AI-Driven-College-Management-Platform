from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api import public, auth, student, faculty, admin, interventions, reports, ai_assist
from app.core.csrf import CSRFMiddleware

app = FastAPI(
    title="Portalitics - Agentic AI-Driven Academic Management Platform",
    description="Proactive Academic Intervention & Student Success System Powered by LangChain & Groq LLM",
    version="2.0.0"
)

# Register custom security middleware
app.add_middleware(CSRFMiddleware)

# Mount Static Files (CSS, JS, Images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include Application Routers
app.include_router(public.router)
app.include_router(auth.router)
app.include_router(student.router)
app.include_router(faculty.router)
app.include_router(admin.router)
app.include_router(interventions.router)
app.include_router(reports.router)
app.include_router(ai_assist.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
