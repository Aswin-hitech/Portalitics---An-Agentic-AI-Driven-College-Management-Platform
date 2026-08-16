from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse
from app.core.security import get_current_user_from_request
from app.services.ai_assist_agent import ai_assist_agent

router = APIRouter(prefix="/api")

@router.post("/ai-assist")
async def ai_assist_endpoint(request: Request, command: str = Form(...)):
    """
    Agentic AI Assist endpoint.
    Receives queries, executes intents, and logs administrative operations.
    """
    user = get_current_user_from_request(request)
    if not user or user.get("role") not in ["faculty", "hod", "admin"]:
        return JSONResponse(
            status_code=403,
            content={
                "status": "error",
                "message": "Unauthorized. Only authenticated staff members (Faculty, HOD, Admin) have access to the AI Assist Command Center."
            }
        )
        
    parsed = ai_assist_agent.parse_intent(command, user)
    result = ai_assist_agent.execute_command(parsed, user)
    
    return JSONResponse({
        "intent": parsed.get("action", "unknown"),
        "plan": parsed.get("plan", []),
        "status": result.get("status", "warning"),
        "message": result.get("message", ""),
        "data": result.get("data"),
        "audit": result.get("audit")
    })
