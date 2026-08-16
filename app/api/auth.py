from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from app.core.templates import templates
from app.core.security import create_access_token, get_current_user_from_request, verify_password
from app.services.mongo_client import mongo_client

router = APIRouter()

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    user = get_current_user_from_request(request)
    if user:
        role = user.get("role", "student")
        if role == "principal":
            return RedirectResponse(url="/principal/dashboard", status_code=303)
        return RedirectResponse(url=f"/{role}/dashboard", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="public/login.html",
        context={"page_title": "User Access & Login - Portalitics", "error": error}
    )

import time
from collections import defaultdict

class RateLimiter:
    """Simple IP-based sliding window rate limiter."""
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self.requests = defaultdict(list)
        
    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        self.requests[ip] = [t for t in self.requests[ip] if now - t < self.window]
        if len(self.requests[ip]) >= self.limit:
            return False
        self.requests[ip].append(now)
        return True

login_limiter = RateLimiter(limit=5, window=60)

@router.post("/login")
async def login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    client_ip = request.client.host if request.client else "unknown"
    if not login_limiter.is_allowed(client_ip):
        return RedirectResponse(url="/login?error=Too many login attempts. Please wait a minute.", status_code=303)

    if not mongo_client._connected:
        return RedirectResponse(url="/login?error=Database connection failed.", status_code=303)
        
    user = mongo_client.db.users.find_one({"email": email})
    if not user:
        return RedirectResponse(url="/login?error=Invalid credentials.", status_code=303)
        
    if not user.get("is_active", True):
        return RedirectResponse(url="/login?error=Account disabled. Contact administrator.", status_code=303)
        
    if not verify_password(password, user.get("password_hash", "")):
        return RedirectResponse(url="/login?error=Invalid credentials.", status_code=303)

    user_id = str(user["_id"])
    role = user.get("role", "student")
    
    # Update last login
    from datetime import datetime
    mongo_client.db.users.update_one({"_id": user["_id"]}, {"$set": {"last_login": datetime.utcnow()}})

    token = create_access_token({"email": email, "role": role, "id": user_id})

    # Direct to correct dashboard based on role
    if role == "student":
        redirect_url = "/student/dashboard"
    elif role == "faculty":
        redirect_url = "/faculty/dashboard"
    elif role == "hod":
        redirect_url = "/faculty/hod-dashboard"
    elif role == "principal":
        redirect_url = "/principal/dashboard"
    elif role == "admin":
        redirect_url = "/admin/dashboard"
    else:
        redirect_url = f"/{role}/dashboard"

    response = RedirectResponse(url=redirect_url, status_code=303)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        secure=True if request.url.scheme == "https" else False,
        samesite="lax"
    )
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    # Registration is disabled. Return a message template.
    return templates.TemplateResponse(
        request=request,
        name="public/register.html",
        context={
            "page_title": "Registration Disabled - Portalitics", 
            "error": "Account access is provided by your institution. Self-registration is disabled."
        }
    )

@router.post("/register")
async def register_submit():
    return RedirectResponse(url="/register", status_code=303)

@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request, error: str = None):
    return templates.TemplateResponse(
        request=request,
        name="public/login.html",
        context={"is_admin_login": True, "page_title": "Admin Secure Login - Portalitics", "error": error}
    )

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_token")
    return response
