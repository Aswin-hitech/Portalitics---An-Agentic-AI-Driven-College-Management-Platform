from fastapi import Request
from fastapi.templating import Jinja2Templates
from app.core.config import settings

def global_context_processor(request: Request):
    token = request.cookies.get("csrf_token")
    if not token:
        token = getattr(request.state, "csrf_token", "")
    return {
        "csrf_token": token,
        "demo_mode": settings.DEMO_MODE
    }

templates = Jinja2Templates(directory="templates", context_processors=[global_context_processor])
