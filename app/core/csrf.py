import secrets
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from app.core.config import settings

class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Custom CSRF protection middleware for Portalitics.
    Forces all state-changing requests (POST, PUT, DELETE) to present a valid token
    cross-referenced with an HTTPOnly session cookie.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        cookie_token = request.cookies.get("csrf_token")
        if not cookie_token:
            cookie_token = secrets.token_hex(32)
        request.state.csrf_token = cookie_token
        
        # Verify CSRF for state-changing forms
        if request.method in ["POST", "PUT", "DELETE"]:
            if settings.APP_ENV != "testing":
                form_token = None
                try:
                    form_data = await request.form()
                    form_token = form_data.get("csrf_token")
                except Exception:
                    pass
                    
                header_token = request.headers.get("x-csrf-token")
                submitted_token = form_token or header_token
                
                # Raise 403 Forbidden on invalid or missing tokens
                if not cookie_token or not submitted_token or not secrets.compare_digest(cookie_token, submitted_token):
                    raise HTTPException(
                        status_code=403,
                        detail="CSRF token validation failed. State-changing requests must include a valid CSRF token."
                    )
                
        # Generate new token if not present in cookie
        response = await call_next(request)
        if "csrf_token" not in request.cookies:
            response.set_cookie(
                "csrf_token",
                cookie_token,
                httponly=True,
                secure=True if request.url.scheme == "https" else False,
                samesite="lax"
            )
            
        return response
