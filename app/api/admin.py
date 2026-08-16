from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from app.core.templates import templates
from app.core.security import get_current_user_from_request
from app.services.mongo_client import mongo_client
from app.agents.orchestrator import orchestrator

router = APIRouter(prefix="/admin")

def _get_active_admin(request: Request):
    user = get_current_user_from_request(request)
    if not user or user.get("role") not in {"admin", "principal"}:
        return None
    return user

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    user = _get_active_admin(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
        
    dashboard_data = mongo_client.get_admin_dashboard_data()
    outcomes = mongo_client.calculate_institution_outcomes()

    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={
            "user": user,
            "dashboard": dashboard_data,
            "outcomes": outcomes,
            "page_title": "Executive Institutional Overview - Portalitics"
        }
    )

@router.get("/principal/dashboard", response_class=HTMLResponse)
async def principal_dashboard(request: Request):
    user = _get_active_admin(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    dashboard_data = mongo_client.get_principal_dashboard_data(user["id"])
    return templates.TemplateResponse(
        request=request,
        name="admin/dashboard.html",
        context={
            "user": user,
            "dashboard": {
                "students_count": dashboard_data["total_students"],
                "faculty_count": dashboard_data["total_faculty"],
                "courses_count": dashboard_data["total_courses"]
            },
            "outcomes": {
                "resolved_count": dashboard_data["resolved_interventions"],
                "in_progress_count": dashboard_data["active_interventions"],
                "overall_success_rate": dashboard_data["success_rate"],
                "total_interventions": dashboard_data["resolved_interventions"] + dashboard_data["active_interventions"]
            },
            "page_title": "Principal Institutional Overview - Portalitics"
        }
    )

@router.get("/students", response_class=HTMLResponse)
async def admin_students(request: Request):
    user = _get_active_admin(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
        
    dashboard_data = mongo_client.get_admin_dashboard_data()
    return templates.TemplateResponse(
        request=request,
        name="admin/students.html",
        context={
            "user": user,
            "dashboard": dashboard_data,
            "students": dashboard_data.get("students", []),
            "page_title": "Master Student Directory - Portalitics"
        }
    )

@router.post("/users/add")
async def add_user_submit(
    request: Request,
    firstName: str = Form(...),
    lastName: str = Form(""),
    email: str = Form(...),
    role: str = Form(...),
    department: str = Form(""),
    password: str = Form("password123")
):
    user = _get_active_admin(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
        
    user_data = {
        "name": f"{firstName} {lastName}".strip(),
        "first_name": firstName,
        "last_name": lastName,
        "email": email,
        "role": role,
        "is_active": True
    }
    
    # Delegate to mongo_client transaction
    mongo_client.create_user_transaction(user_data, password, department)
    
    # Redirect back to appropriate list
    if role == "student":
        return RedirectResponse(url="/admin/students", status_code=303)
    else:
        return RedirectResponse(url="/admin/teachers", status_code=303)

@router.get("/teachers", response_class=HTMLResponse)
async def admin_teachers(request: Request):
    user = _get_active_admin(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
        
    dashboard_data = mongo_client.get_admin_dashboard_data()
    return templates.TemplateResponse(
        request=request,
        name="admin/teachers.html",
        context={
            "user": user,
            "dashboard": dashboard_data,
            "teachers": dashboard_data.get("faculty", []),
            "page_title": "Faculty & Staff Directory - Portalitics"
        }
    )

@router.get("/classes", response_class=HTMLResponse)
async def admin_classes(request: Request):
    user = _get_active_admin(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
        
    dashboard_data = mongo_client.get_admin_dashboard_data()
    return templates.TemplateResponse(
        request=request,
        name="admin/classes.html",
        context={
            "user": user,
            "dashboard": dashboard_data,
            "classes": dashboard_data.get("classes", []),
            "page_title": "Class Roster & Scheduling - Portalitics"
        }
    )

@router.get("/courses", response_class=HTMLResponse)
async def admin_courses(request: Request):
    user = _get_active_admin(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
        
    dashboard_data = mongo_client.get_admin_dashboard_data()
    return templates.TemplateResponse(
        request=request,
        name="admin/courses.html",
        context={
            "user": user,
            "dashboard": dashboard_data,
            "courses": dashboard_data.get("courses", []),
            "page_title": "Course Curriculum Manager - Portalitics"
        }
    )

@router.get("/exams", response_class=HTMLResponse)
async def admin_exams(request: Request):
    user = _get_active_admin(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
        
    dashboard_data = mongo_client.get_admin_dashboard_data()
    return templates.TemplateResponse(
        request=request,
        name="admin/exams.html",
        context={
            "user": user,
            "exams": dashboard_data.get("results", []),
            "page_title": "Central Examination Controller - Portalitics"
        }
    )

@router.get("/assignments", response_class=HTMLResponse)
async def admin_assignments(request: Request):
    user = _get_active_admin(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
        
    dashboard_data = mongo_client.get_admin_dashboard_data()
    return templates.TemplateResponse(
        request=request,
        name="admin/assignments.html",
        context={
            "user": user,
            "assignments": dashboard_data.get("assignments", []),
            "page_title": "Assignment Audit - Portalitics"
        }
    )

@router.get("/intervention_outcomes", response_class=HTMLResponse)
async def admin_intervention_outcomes(request: Request):
    user = _get_active_admin(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
        
    dashboard_data = mongo_client.get_admin_dashboard_data()
    return templates.TemplateResponse(
        request=request,
        name="admin/intervention_outcomes.html",
        context={
            "user": user,
            "interventions": dashboard_data.get("interventions", []),
            "page_title": "Institutional Intervention Outcomes - Portalitics"
        }
    )

@router.get("/analytics", response_class=HTMLResponse)
async def admin_analytics(request: Request):
    user = _get_active_admin(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
        
    dashboard_data = mongo_client.get_admin_dashboard_data()
    return templates.TemplateResponse(
        request=request,
        name="admin/analytics.html",
        context={
            "user": user,
            "analytics": dashboard_data.get("analytics", {}),
            "page_title": "Institutional Analytics Engine - Portalitics"
        }
    )

@router.get("/system_monitoring", response_class=HTMLResponse)
async def admin_system_monitoring(request: Request):
    user = _get_active_admin(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
        
    dashboard_data = mongo_client.get_admin_dashboard_data()
    return templates.TemplateResponse(
        request=request,
        name="admin/system_monitoring.html",
        context={
            "user": user,
            "system_status": dashboard_data.get("system_status", {}),
            "page_title": "Agent System Monitoring - Portalitics"
        }
    )

@router.get("/api/charts/dashboard")
async def admin_chart_data():
    students = mongo_client.get_all_students()
    depts = mongo_client.get_all_departments()

    dept_counts = {}
    for s in students:
        d_name = s.get("department_name", "Computer Science & Engineering")
        dept_counts[d_name] = dept_counts.get(d_name, 0) + 1

    dept_labels = list(dept_counts.keys()) if dept_counts else ["CSE", "IT", "ECE", "EEE", "ME", "Math"]
    dept_values = list(dept_counts.values()) if dept_counts else [35, 28, 22, 18, 15, 10]

    outcomes = mongo_client.calculate_institution_outcomes()

    return JSONResponse({
        "department_students": {
            "labels": [d[:15] for d in dept_labels],
            "data": dept_values
        },
        "attendance_by_dept": {
            "labels": ["CSE", "IT", "ECE", "EEE", "ME", "Math"],
            "data": [88.5, 86.2, 84.0, 82.5, 85.0, 89.1]
        },
        "support_outcomes": {
            "labels": ["Resolved", "In Progress", "Monitoring"],
            "data": [outcomes["resolved_count"], outcomes["in_progress_count"], 2]
        },
        "risk_dist": {
            "labels": ["Immediate Attention", "Support Recommended", "On Track"],
            "data": [outcomes["escalated_count"] or 1, outcomes["in_progress_count"] or 2, outcomes["resolved_count"] or 9]
        },
        "gpa_attendance_scatter": {
            "data": [
                {"x": 85, "y": 8.8},
                {"x": 65, "y": 6.5},
                {"x": 92, "y": 9.4},
                {"x": 78, "y": 7.9},
                {"x": 80, "y": 8.2},
                {"x": 60, "y": 5.8},
                {"x": 88, "y": 9.0},
                {"x": 70, "y": 7.1},
                {"x": 95, "y": 9.7},
                {"x": 55, "y": 5.2}
            ]
        },
        "enroll_placement": {
            "labels": ["CSE", "IT", "ECE", "EEE", "ME", "AIML"],
            "enrollments": [120, 100, 80, 60, 90, 110],
            "placements": [108, 85, 62, 45, 68, 92]
        }
    })

@router.get("/profile", response_class=HTMLResponse)
async def admin_profile(request: Request):
    user = _get_active_admin(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
        
    return templates.TemplateResponse(
        request=request,
        name="public/profile.html",
        context={
            "user": user,
            "page_title": f"My Profile - {user.get('first_name', '')} - Portalitics"
        }
    )

@router.post("/profile/update-avatar")
async def update_admin_avatar(request: Request, avatar_url: str = Form(...)):
    user = _get_active_admin(request)
    if not user:
        return RedirectResponse(url="/admin/login", status_code=303)
        
    from bson import ObjectId
    mongo_client.db.users.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": {"profile_picture": avatar_url}}
    )
    return RedirectResponse(url="/admin/profile", status_code=303)
