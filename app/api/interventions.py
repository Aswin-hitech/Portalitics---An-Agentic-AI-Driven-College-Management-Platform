from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
from app.core.security import get_current_user_from_request
from app.services.intervention_service import intervention_service
from app.agents.orchestrator import orchestrator
from app.services.mongo_client import mongo_client
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/interventions")

def _can_modify_interventions(user):
    return bool(user and user.get("role") in {"faculty", "hod", "principal", "admin"})

@router.post("/update_status")
async def update_status(
    request: Request,
    margin_id: str = Form(...),
    status: str = Form(...),
    notes: str = Form("")
):
    user = get_current_user_from_request(request)
    if not _can_modify_interventions(user):
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=403)
    intervention_service.update_intervention_status(margin_id, status, notes)
    return RedirectResponse(url=f"/faculty/intervention_details/{margin_id}", status_code=303)

# Re-map legacy variable name for parameter compatibility
@router.post("/update_status_legacy")
async def update_status_legacy(
    request: Request,
    intervention_id: str = Form(...),
    status: str = Form(...),
    notes: str = Form("")
):
    user = get_current_user_from_request(request)
    if not _can_modify_interventions(user):
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=403)
    intervention_service.update_intervention_status(intervention_id, status, notes)
    return RedirectResponse(url=f"/faculty/intervention_details/{intervention_id}", status_code=303)

@router.post("/initiate")
async def initiate_intervention(
    request: Request,
    student_id: str = Form(...),
    student_name: str = Form(...)
):
    user = get_current_user_from_request(request)
    if not _can_modify_interventions(user):
        return JSONResponse({"status": "error", "message": "Unauthorized"}, status_code=403)
    teacher_id = user["id"] if user else "tch_001"
    teacher_name = user["name"] if user else "Faculty Instructor"

    # Query real performance and risk evaluation from orchestrator
    event_result = orchestrator.route_event("intervention_initiated", student_id, "faculty")
    report = event_result.get("formatted_report", {})
    risk = event_result.get("support_evaluation", {})
    perf = event_result.get("performance_metrics", {})
    
    # Resolve student course name from MongoDB
    student_doc = mongo_client.get_user_by_id(student_id)
    course_name = student_doc.get("course", "B.Tech Computer Science & Engineering") if student_doc else "B.Tech Computer Science & Engineering"
    
    # Calculate action code based on tier
    tier = report.get("priority_tier", "Support Recommended")
    action_code = "CRITICAL" if tier == "Immediate Attention Needed" else "NEEDS_ATTENTION"
    
    rec = {
        "course_name": course_name,
        "priority_tier": tier,
        "action_code": action_code,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "evaluation_due": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
        "key_signals": {
            "attendance": report.get("key_signals", {}).get("attendance", "85%"),
            "grade_trend": report.get("key_signals", {}).get("exam_trend", "Stable")
        },
        "suggested_action": report.get("suggested_action", "Provide personalized academic mentoring"),
        "outcome_metrics": {
            "initial_attendance": float(perf.get("attendance_percentage", 85.0)),
            "current_attendance": float(perf.get("attendance_percentage", 85.0)),
            "initial_grade_avg": float(perf.get("grade_average", 70.0)),
            "current_grade_avg": float(perf.get("grade_average", 70.0)),
            "improvement_status": "Monitoring Initiated"
        }
    }
    
    entry = intervention_service.initiate_intervention(
        student_id=student_id,
        student_name=student_name,
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        recommendation=rec
    )
    return RedirectResponse(url=f"/faculty/intervention_details/{entry['id']}", status_code=303)
