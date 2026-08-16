from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.core.templates import templates
from app.core.security import get_current_user_from_request
from app.services.mongo_client import mongo_client
from app.agents.orchestrator import orchestrator

router = APIRouter(prefix="/faculty")

@router.post("/profile/update-avatar")
async def update_avatar(request: Request, avatar_url: str = Form(...)):
    user = _get_active_faculty(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    from bson import ObjectId
    mongo_client.db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": {"profile_picture": avatar_url}}
    )
    return RedirectResponse(url="/faculty/profile", status_code=303)

def _get_active_faculty(request: Request):
    user = get_current_user_from_request(request)
    if not user or user.get("role") not in ["faculty", "hod"]:
        return None
    return user

@router.get("/dashboard", response_class=HTMLResponse)
async def faculty_dashboard(request: Request):
    user = _get_active_faculty(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    dashboard_data = mongo_client.get_faculty_dashboard_data(user["id"])
    
    return templates.TemplateResponse(
        request=request,
        name="faculty/dashboard.html",
        context={
            "user": user,
            "dashboard": dashboard_data,
            "page_title": f"Faculty Dashboard - {user.get('first_name', 'Faculty')} - Portalitics"
        }
    )

@router.get("/hod-dashboard", response_class=HTMLResponse)
async def hod_dashboard(request: Request):
    user = get_current_user_from_request(request)
    if not user or user.get("role") != "hod":
        return RedirectResponse(url="/login", status_code=303)
        
    dashboard_data = mongo_client.get_hod_dashboard_data(user["id"])
    
    return templates.TemplateResponse(
        request=request,
        name="faculty/hod_dashboard.html",
        context={
            "user": user,
            "dashboard": dashboard_data,
            "page_title": f"HOD Departmental Dashboard - Portalitics"
        }
    )

@router.get("/classes", response_class=HTMLResponse)
async def faculty_classes(request: Request):
    user = _get_active_faculty(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    dashboard_data = mongo_client.get_faculty_dashboard_data(user["id"])
    
    return templates.TemplateResponse(
        request=request,
        name="faculty/classes.html",
        context={
            "user": user,
            "dashboard": dashboard_data,
            "classes": dashboard_data.get("classes", []),
            "page_title": "My Classes - Portalitics"
        }
    )

@router.get("/students", response_class=HTMLResponse)
async def faculty_students(request: Request):
    user = _get_active_faculty(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    dashboard_data = mongo_client.get_faculty_dashboard_data(user["id"])
    
    return templates.TemplateResponse(
        request=request,
        name="faculty/students.html",
        context={
            "user": user,
            "dashboard": dashboard_data,
            "students": dashboard_data.get("students", []),
            "page_title": "Student Directory - Portalitics"
        }
    )

@router.get("/attendance", response_class=HTMLResponse)
async def faculty_attendance(request: Request):
    user = _get_active_faculty(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    dashboard_data = mongo_client.get_faculty_dashboard_data(user["id"])
    
    return templates.TemplateResponse(
        request=request,
        name="faculty/attendance.html",
        context={
            "user": user,
            "dashboard": dashboard_data,
            "classes": dashboard_data.get("classes", []),
            "page_title": "Mark Attendance - Portalitics"
        }
    )

@router.post("/attendance/mark")
async def mark_attendance_submit(request: Request, student_id: str = Form(...), subject: str = Form(...), status: str = Form(...)):
    mongo_client.record_attendance(student_id, subject, status)
    orchestrator.route_event("attendance_updated", student_id, "faculty")
    return RedirectResponse(url="/faculty/attendance", status_code=303)

@router.get("/assignments", response_class=HTMLResponse)
async def faculty_assignments(request: Request):
    user = _get_active_faculty(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    dashboard_data = mongo_client.get_faculty_dashboard_data(user["id"])
    
    return templates.TemplateResponse(
        request=request,
        name="faculty/assignments.html",
        context={
            "user": user,
            "dashboard": dashboard_data,
            "assignments": dashboard_data.get("assignments", []),
            "page_title": "Manage Assignments - Portalitics"
        }
    )

@router.post("/assignments/create")
async def create_assignment_submit(title: str = Form(...), course: str = Form(...), due_date: str = Form(...)):
    mongo_client.create_assignment({
        "assignment_id": f"ASG_{len(mongo_client.get_all_assignments())+1:03d}",
        "title": title,
        "course_name": course,
        "due_date": due_date
    })
    return RedirectResponse(url="/faculty/assignments", status_code=303)

@router.get("/exams", response_class=HTMLResponse)
async def faculty_exams(request: Request):
    user = _get_active_faculty(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    dashboard_data = mongo_client.get_faculty_dashboard_data(user["id"])
    
    return templates.TemplateResponse(
        request=request,
        name="faculty/exams.html",
        context={
            "user": user,
            "students": dashboard_data.get("students", []),
            "classes": dashboard_data.get("classes", []),
            "page_title": "Exam Results Entry - Portalitics"
        }
    )

@router.post("/exams/record")
async def record_exam_submit(student_id: str = Form(...), exam_name: str = Form(...), subject: str = Form(...), score: float = Form(...)):
    exam_id = f"EXM_{len(mongo_client.get_all_exams())+1:03d}"
    mongo_client.record_exam_mark(student_id, exam_id, exam_name, subject, score)
    orchestrator.route_event("exam_result_added", student_id, "faculty")
    return RedirectResponse(url="/faculty/exams", status_code=303)

@router.get("/intervention_queue", response_class=HTMLResponse)
async def faculty_intervention_queue(request: Request):
    user = _get_active_faculty(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    dashboard_data = mongo_client.get_faculty_dashboard_data(user["id"])
    
    return templates.TemplateResponse(
        request=request,
        name="faculty/intervention_queue.html",
        context={
            "user": user,
            "dashboard": dashboard_data,
            "queue": dashboard_data.get("intervention_queue", []),
            "page_title": "Intervention Queue - Portalitics"
        }
    )

@router.get("/intervention_details/{intervention_id}", response_class=HTMLResponse)
async def faculty_intervention_details(request: Request, intervention_id: str):
    user = _get_active_faculty(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    intervention = mongo_client.get_intervention_by_id(intervention_id) or {}
    
    return templates.TemplateResponse(
        request=request,
        name="faculty/intervention_details.html",
        context={
            "user": user,
            "item": intervention,
            "intervention_id": intervention_id,
            "page_title": "Intervention Case - Portalitics"
        }
    )

@router.get("/api/charts")
async def faculty_chart_data(request: Request):
    user = _get_active_faculty(request)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
    dashboard_data = mongo_client.get_faculty_dashboard_data(user["id"])
    queue = dashboard_data.get("intervention_queue", [])

    critical = sum(1 for q in queue if q.get("action_code") == "CRITICAL")
    needs_attention = sum(1 for q in queue if q.get("action_code") == "NEEDS_ATTENTION")
    monitor = max(0, len(queue) - critical - needs_attention)

    return JSONResponse({
        "attendance_dist": {
            "labels": ["> 90%", "75% - 90%", "< 75%"],
            "data": [65, 25, 10]
        },
        "score_dist": {
            "labels": ["Grade A (80-100)", "Grade B (65-79)", "Grade C (50-64)", "Needs Support (<50)"],
            "data": [22, 14, 8, 4]
        },
        "support_queue_dist": {
            "labels": ["Immediate Attention", "Support Recommended", "On Track"],
            "data": [critical, needs_attention, monitor or 1]
        },
        "intervention_trend": {
            "labels": ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5"],
            "data": [8, 12, 5, 6, 3]
        },
        "subject_averages": {
            "labels": ["DBMS", "OS", "ML", "Network Security"],
            "class_avg": [74, 68, 82, 70],
            "dept_avg": [78, 72, 79, 74]
        }
    })

@router.get("/profile", response_class=HTMLResponse)
async def faculty_profile(request: Request):
    user = _get_active_faculty(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    return templates.TemplateResponse(
        request=request,
        name="public/profile.html",
        context={
            "user": user,
            "page_title": f"My Profile - {user.get('first_name', '')} - Portalitics"
        }
    )
