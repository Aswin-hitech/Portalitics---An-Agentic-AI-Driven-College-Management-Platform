from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from app.core.templates import templates
from app.core.security import get_current_user_from_request
from app.services.mongo_client import mongo_client

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    user = get_current_user_from_request(request)
    featured_courses = list(mongo_client.db.courses.find().limit(3))
    # Convert ObjectIds for template rendering
    for c in featured_courses:
        c["id"] = str(c.pop("_id"))
        if "title" not in c and "name" in c:
            c["title"] = c["name"]
        if "description" not in c:
            c["description"] = f"Professional degree program focusing on theory, practice, and research in {c.get('title', 'Engineering')}."
        if "credits" not in c:
            c["credits"] = 4
        
    top_teachers = list(mongo_client.db.users.find({"role": "faculty"}).limit(4))
    for t in top_teachers:
        t["id"] = str(t.pop("_id"))
        
    return templates.TemplateResponse(
        request=request,
        name="public/index.html",
        context={
            "user": user,
            "courses": featured_courses,
            "teachers": top_teachers,
            "page_title": "Portalitics - Agentic AI Academic Platform"
        }
    )

@router.get("/explore", response_class=HTMLResponse)
async def explore_page(request: Request, q: str = "", category: str = ""):
    user = get_current_user_from_request(request)
    
    query = {}
    if q:
        query["name"] = {"$regex": q, "$options": "i"}
        
    courses_cursor = mongo_client.db.courses.find(query).limit(6)
    courses_list = []
    for c in courses_cursor:
        c_dict = {"id": str(c["_id"]), **{k:v for k,v in c.items() if k!="_id"}}
        c_dict["title"] = c_dict.get("title", c_dict.get("name", "B.Tech Course"))
        c_dict["description"] = c_dict.get("description", f"Degree course in {c_dict['title']}.")
        c_dict["credits"] = c_dict.get("credits", 4)
        courses_list.append(c_dict)
    
    dept_cursor = mongo_client.db.departments.find()
    dept_list = [{"id": str(d["_id"]), **{k:v for k,v in d.items() if k!="_id"}} for d in dept_cursor]
    
    notices_cursor = mongo_client.db.notices.find().sort("createdAt", -1).limit(4)
    notice_list = [{"id": str(n["_id"]), **{k:v for k,v in n.items() if k!="_id"}} for n in notices_cursor]
    
    events_cursor = mongo_client.db.events.find().sort("date", 1).limit(4)
    event_list = [{"id": str(e["_id"]), **{k:v for k,v in e.items() if k!="_id"}} for e in events_cursor]

    return templates.TemplateResponse(
        request=request,
        name="public/explore.html",
        context={
            "user": user,
            "courses": courses_list,
            "departments": dept_list,
            "notices": notice_list,
            "events": event_list,
            "search_query": q,
            "selected_category": category,
            "page_title": "Explore Campus - Portalitics"
        }
    )


@router.get("/courses", response_class=HTMLResponse)
async def courses_page(request: Request, q: str = "", category: str = ""):
    user = get_current_user_from_request(request)
    query = {}
    if q:
        query["name"] = {"$regex": q, "$options": "i"}
        
    courses_cursor = mongo_client.db.courses.find(query)
    courses_list = []
    for c in courses_cursor:
        c_dict = {"id": str(c["_id"]), **{k:v for k,v in c.items() if k!="_id"}}
        c_dict["title"] = c_dict.get("title", c_dict.get("name", "B.Tech Course"))
        c_dict["description"] = c_dict.get("description", f"Degree course in {c_dict['title']}.")
        c_dict["credits"] = c_dict.get("credits", 4)
        courses_list.append(c_dict)
    
    return templates.TemplateResponse(
        request=request,
        name="public/courses.html",
        context={
            "user": user,
            "courses": courses_list,
            "search_query": q,
            "selected_category": category,
            "page_title": "Course Directory - Portalitics"
        }
    )

@router.get("/courses/{course_id}", response_class=HTMLResponse)
async def course_details_page(request: Request, course_id: str):
    user = get_current_user_from_request(request)
    from bson.objectid import ObjectId
    try:
        course = mongo_client.db.courses.find_one({"_id": ObjectId(course_id)})
    except:
        course = None
        
    if not course:
        return RedirectResponse(url="/courses", status_code=303)
        
    course["id"] = str(course.pop("_id"))
    course["title"] = course.get("title", course.get("name", "B.Tech Course"))
    course["description"] = course.get("description", f"Degree course in {course['title']}.")
    course["credits"] = course.get("credits", 4)
        
    return templates.TemplateResponse(
        request=request,
        name="public/course_details.html",
        context={
            "user": user,
            "course": course,
            "page_title": f"{course.get('code', '')}: {course.get('name', '')} - Portalitics"
        }
    )

@router.get("/departments", response_class=HTMLResponse)
async def departments_page(request: Request):
    user = get_current_user_from_request(request)
    dept_cursor = mongo_client.db.departments.find()
    departments = [{"id": str(d["_id"]), **{k:v for k,v in d.items() if k!="_id"}} for d in dept_cursor]
    
    return templates.TemplateResponse(
        request=request,
        name="public/departments.html",
        context={
            "user": user,
            "departments": departments,
            "page_title": "Academic Departments - Portalitics"
        }
    )

@router.get("/events", response_class=HTMLResponse)
async def events_page(request: Request):
    user = get_current_user_from_request(request)
    events_cursor = mongo_client.db.events.find().sort("date", 1)
    events = [{"id": str(e["_id"]), **{k:v for k,v in e.items() if k!="_id"}} for e in events_cursor]
    
    return templates.TemplateResponse(
        request=request,
        name="public/events.html",
        context={
            "user": user,
            "events": events,
            "page_title": "Campus Events - Portalitics"
        }
    )

@router.get("/notices", response_class=HTMLResponse)
async def notices_page(request: Request):
    user = get_current_user_from_request(request)
    notices_cursor = mongo_client.db.notices.find().sort("createdAt", -1)
    notices = [{"id": str(n["_id"]), **{k:v for k,v in n.items() if k!="_id"}} for n in notices_cursor]
    
    return templates.TemplateResponse(
        request=request,
        name="public/notices.html",
        context={
            "user": user,
            "notices": notices,
            "page_title": "Campus Notices - Portalitics"
        }
    )

@router.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    user = get_current_user_from_request(request)
    return templates.TemplateResponse(
        request=request,
        name="public/contact.html",
        context={
            "user": user,
            "page_title": "Contact & Support Desk - Portalitics"
        }
    )

@router.post("/contact")
async def contact_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...)
):
    user = get_current_user_from_request(request)
    return templates.TemplateResponse(
        request=request,
        name="public/contact.html",
        context={
            "user": user,
            "success_message": "Thank you for reaching out! Our academic support team will get back to you shortly.",
            "page_title": "Contact & Support Desk - Portalitics"
        }
    )

@router.get("/settings")
async def settings_page(request: Request):
    user = get_current_user_from_request(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
        
    role = user.get("role", "student")
    if role == "hod":
        return RedirectResponse(url="/faculty/profile", status_code=303)
    else:
        return RedirectResponse(url=f"/{role}/profile", status_code=303)


