from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200
    assert "Portalitics" in response.text
    assert "Featured Academic Courses" in response.text

def test_courses_directory():
    response = client.get("/courses")
    assert response.status_code == 200
    assert "Course Directory" in response.text

def test_course_details():
    # Should redirect to /courses since crs_001 is invalid, and return 200 (followed redirect)
    response = client.get("/courses/crs_001")
    assert response.status_code == 200

def test_student_dashboard():
    # Login as student first to establish session cookie
    login_response = client.post("/login", data={"email": "student0@college.edu", "password": "password123"})
    assert login_response.status_code == 200
    
    response = client.get("/student/dashboard")
    assert response.status_code == 200
    assert "Dashboard" in response.text

def test_teacher_intervention_queue():
    # Login as faculty first
    login_response = client.post("/login", data={"email": "faculty0@college.edu", "password": "password123"})
    assert login_response.status_code == 200
    
    response = client.get("/faculty/intervention_queue")
    assert response.status_code == 200
    assert "Learning Support Queue" in response.text

def test_admin_dashboard():
    # Login as admin first
    login_response = client.post("/login", data={"email": "admin@college.edu", "password": "password123"})
    assert login_response.status_code == 200
    
    response = client.get("/admin/dashboard")
    assert response.status_code == 200
    assert "Institutional Overview" in response.text or "Overview" in response.text

def test_ai_assist_permissions():
    # Login as student
    login_response = client.post("/login", data={"email": "student0@college.edu", "password": "password123"})
    assert login_response.status_code == 200
    
    # Attempt AI Assist command as student
    response = client.post("/api/ai-assist", data={"command": "Show all AIML students with attendance below 75%"})
    assert response.status_code == 403
    assert "Unauthorized" in response.json()["message"]

def test_ai_assist_execute():
    # Login as faculty
    login_response = client.post("/login", data={"email": "faculty0@college.edu", "password": "password123"})
    assert login_response.status_code == 200
    
    # Query attendance
    response = client.post("/api/ai-assist", data={"command": "Show all AIML students with attendance below 75%"})
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert "attendance" in res_data["intent"]
    
    # Update student marks
    response = client.post("/api/ai-assist", data={"command": "Find Aswin from the AIML department and update his OOPS mark to 92"})
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert "update_marks" in res_data["intent"]
    assert res_data["audit"] is not None

def test_student_assignment_submit():
    # Login as student
    login_response = client.post("/login", data={"email": "student0@college.edu", "password": "password123"})
    assert login_response.status_code == 200
    
    # Retrieve first seeded assignment
    from app.services.mongo_client import mongo_client
    assignment = mongo_client.db.assignments.find_one()
    assert assignment is not None
    asg_id = str(assignment["_id"])
    
    # Submit assignment coursework
    response = client.post("/student/assignments/submit", data={
        "assignment_id": asg_id,
        "submission_text": "Here is my completed homework solution drive link."
    })
    assert response.status_code == 200 or response.status_code == 303

def test_ai_assist_missing_student():
    # Login as faculty
    login_response = client.post("/login", data={"email": "faculty0@college.edu", "password": "password123"})
    assert login_response.status_code == 200
    
    # Query updates for non-existent student
    response = client.post("/api/ai-assist", data={"command": "Find HarryPotter from AIML and update OOPS mark to 95"})
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "error"
    assert "was not found" in res_data["message"]

def test_ai_assist_unauthenticated():
    # Query AI Assist without logging in
    client.cookies.clear()
    response = client.post("/api/ai-assist", data={"command": "Show all AIML students with attendance below 75%"})
    assert response.status_code == 403


