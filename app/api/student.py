from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.core.templates import templates
from app.core.security import get_current_user_from_request
from app.services.mongo_client import mongo_client
from app.agents.orchestrator import orchestrator

router = APIRouter(prefix="/student")

def _get_active_student(request: Request):
    user = get_current_user_from_request(request)
    if not user or user.get("role") != "student":
        return None
    return user

@router.get("/dashboard", response_class=HTMLResponse)
async def student_dashboard(request: Request):
    user = _get_active_student(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    dashboard_data = mongo_client.get_student_dashboard_data(user["id"])
    
    # Run orchestrator for student insights
    agent_output = orchestrator.route_event("dashboard_loaded", user["id"], "student")

    return templates.TemplateResponse(
        request=request,
        name="student/dashboard.html",
        context={
            "user": user,
            "dashboard": dashboard_data,
            "courses": dashboard_data.get("classes", []),
            "history": dashboard_data,
            "metrics": agent_output.get("performance_metrics", {}),
            "ai_insights": agent_output.get("formatted_report", ""),
            "support_eval": agent_output.get("support_evaluation", ""),
            "page_title": f"Student Dashboard - {user.get('first_name', 'Student')} - Portalitics"
        }
    )

@router.get("/profile", response_class=HTMLResponse)
async def student_profile(request: Request):
    user = _get_active_student(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    dashboard_data = mongo_client.get_student_dashboard_data(user["id"])
    
    return templates.TemplateResponse(
        request=request,
        name="public/profile.html",
        context={
            "user": user,
            "profile": user, # Profile details are directly on user
            "page_title": f"My Profile - {user.get('first_name', '')} - Portalitics"
        }
    )

@router.post("/profile/update-avatar")
async def update_avatar(request: Request, avatar_url: str = Form(...)):
    user = _get_active_student(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    from bson import ObjectId
    mongo_client.db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": {"profile_picture": avatar_url}}
    )
    return RedirectResponse(url="/student/profile", status_code=303)

@router.get("/courses", response_class=HTMLResponse)
async def student_courses(request: Request):
    user = _get_active_student(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    dashboard_data = mongo_client.get_student_dashboard_data(user["id"])
    
    return templates.TemplateResponse(
        request=request,
        name="student/courses.html",
        context={
            "user": user,
            "enrollments": dashboard_data.get("classes", []),
            "page_title": "My Courses - Portalitics"
        }
    )

@router.get("/timetable", response_class=HTMLResponse)
async def student_timetable(request: Request):
    user = _get_active_student(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    dashboard_data = mongo_client.get_student_dashboard_data(user["id"])
    
    return templates.TemplateResponse(
        request=request,
        name="student/timetable.html",
        context={
            "user": user,
            "timetable": dashboard_data.get("timetable", []),
            "page_title": "My Timetable - Portalitics"
        }
    )

@router.get("/attendance", response_class=HTMLResponse)
async def student_attendance(request: Request):
    user = _get_active_student(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    history = mongo_client.get_student_academic_history(user["id"])
    return templates.TemplateResponse(
        request=request,
        name="student/attendance.html",
        context={
            "user": user,
            "attendance": history["attendance"],
            "page_title": "Attendance - Portalitics"
        }
    )

@router.get("/grades", response_class=HTMLResponse)
async def student_grades(request: Request):
    user = _get_active_student(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    history = mongo_client.get_student_academic_history(user["id"])
    return templates.TemplateResponse(
        request=request,
        name="student/grades.html",
        context={
            "user": user,
            "exams": history["exams"],
            "page_title": "Exams & Results - Portalitics"
        }
    )

@router.get("/progress", response_class=HTMLResponse)
async def student_progress(request: Request):
    user = _get_active_student(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    agent_output = orchestrator.route_event("progress_viewed", user["id"], "student")
    return templates.TemplateResponse(
        request=request,
        name="student/progress.html",
        context={
            "user": user,
            "ai_report": agent_output["formatted_report"],
            "metrics": agent_output["performance_metrics"],
            "eval": agent_output["support_evaluation"],
            "page_title": "Academic Performance Insights - Portalitics"
        }
    )

@router.get("/assignments", response_class=HTMLResponse)
async def student_assignments(request: Request):
    user = _get_active_student(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    dashboard_data = mongo_client.get_student_dashboard_data(user["id"])
    return templates.TemplateResponse(
        request=request,
        name="student/assignments.html",
        context={
            "user": user,
            "dashboard": dashboard_data,
            "assignments": dashboard_data.get("assignments", []),
            "page_title": "My Assignments - Portalitics"
        }
    )

# --- Dynamic Chart API for Student Dashboard ---
@router.get("/api/charts")
async def student_chart_data(request: Request):
    user = _get_active_student(request)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
    history = mongo_client.get_student_academic_history(user["id"])

    att_records = history.get("attendance", [])
    dates = [a.get("date", "")[-5:] for a in reversed(att_records[:7])] or ["Mon", "Tue", "Wed", "Thu", "Fri"]
    att_trend = [85, 80, 75, 72, 78, 82, 85][:len(dates)]

    exams = history.get("exams", [])
    exam_labels = [e.get("exam_name", "Test")[:10] for e in exams] or ["Unit 1", "Unit 2", "Mid-Term"]
    exam_scores = [float(e.get("score", 70)) for e in exams] or [78, 64, 55]

    return JSONResponse({
        "attendance_trend": {
            "labels": dates,
            "data": att_trend
        },
        "exam_scores": {
            "labels": exam_labels,
            "data": exam_scores
        },
        "cgpa_progression": {
            "labels": ["Sem 1", "Sem 2", "Sem 3", "Sem 4"],
            "data": [8.1, 8.3, 8.2, 8.4]
        },
        "assignment_status": {
            "labels": ["Completed", "Pending", "Late"],
            "data": [12, 3, 1]
        },
        "exam_scatter": {
            "data": [
                {"x": 80, "y": 8.5},
                {"x": 75, "y": 7.8},
                {"x": 90, "y": 9.2},
                {"x": 65, "y": 6.8},
                {"x": 85, "y": 8.4},
                {"x": 70, "y": 7.2},
                {"x": 95, "y": 9.6}
            ]
        }
    })

@router.post("/assignments/submit")
async def submit_assignment(
    request: Request,
    assignment_id: str = Form(...),
    submission_text: str = Form(...)
):
    user = _get_active_student(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    from bson import ObjectId
    from datetime import datetime
    
    asg = mongo_client.db.assignments.find_one({"_id": ObjectId(assignment_id)})
    asg_title = asg.get("title", "Coursework Submission") if asg else "Coursework Submission"
    asg_due = asg.get("due_date", "2026-08-15") if asg else "2026-08-15"
    
    try:
        due_date = datetime.strptime(asg_due, "%Y-%m-%d")
    except Exception:
        due_date = datetime.now()
        
    is_late = datetime.now() > due_date
    
    mongo_client.db.submissions.insert_one({
        "assignment_id": ObjectId(assignment_id),
        "student_id": ObjectId(user["id"]),
        "title": asg_title,
        "content": submission_text,
        "status": "submitted",
        "due_date": asg_due,
        "is_late": is_late,
        "submitted_at": datetime.utcnow()
    })
    
    # Trigger academic risk analysis
    orchestrator.route_event("assignment_submitted", user["id"], "student")
    
    return RedirectResponse(url="/student/assignments", status_code=303)
