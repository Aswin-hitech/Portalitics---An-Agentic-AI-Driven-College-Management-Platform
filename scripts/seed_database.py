import sys
import random
from datetime import datetime, timedelta
from app.services.mongo_client import mongo_client
from bson import ObjectId

# Password Hashing import
try:
    from app.core.security import hash_password as get_password_hash
except ImportError:
    import passlib.hash
    def get_password_hash(pwd):
        return passlib.hash.bcrypt.hash(pwd)

def seed_database():
    if not mongo_client.is_connected():
        print("[ERROR] Could not connect to MongoDB server. Please ensure MongoDB is running.")
        sys.exit(1)

    print("Clearing collections...")
    collections = [
        "users", "institution", "departments", "courses", "academicYears", "semesters",
        "classes", "subjects", "facultyAssignments", "attendance", "assignments",
        "submissions", "exams", "results", "timetables", "studentRequests",
        "facultyTasks", "notifications", "notices", "events", "hostels",
        "hostelAllocations", "transport", "certifications", "projects",
        "internships", "placements", "interventions", "academicInsights",
        "aiRecommendations", "riskScores", "reports", "analytics", "auditLogs"
    ]
    for col in collections:
        mongo_client.db[col].delete_many({})

    hashed_password = get_password_hash("password123")

    # 1. Institution Setup
    institution = {
        "name": "Portalitics Institute of Technology",
        "code": "PIT",
        "address": "123 Education Boulevard, Tech City, 600097",
        "academic_year": "2026-2027",
        "contact": {
            "email": "info@pit.edu",
            "phone": "+91-44-24501234",
            "support": "support@pit.edu"
        },
        "principal": {
            "name": "Dr. Skinner",
            "email": "principal@college.edu",
            "phone": "+91-9876543211"
        }
    }
    mongo_client.db.institution.insert_one(institution)
    print("Seeded Institution details.")

    # 2. Seed Departments
    dept_codes = ["AIML", "AIDS", "CSE", "Cyber Security", "ECE", "EEE", "MECH", "IT"]
    dept_names = {
        "AIML": "Artificial Intelligence and Machine Learning",
        "AIDS": "Artificial Intelligence and Data Science",
        "CSE": "Computer Science and Engineering",
        "Cyber Security": "Cyber Security and Forensics",
        "ECE": "Electronics and Communication Engineering",
        "EEE": "Electrical and Electronics Engineering",
        "MECH": "Mechanical Engineering",
        "IT": "Information Technology"
    }
    
    dept_ids = {}
    for code in dept_codes:
        dept_ids[code] = mongo_client.db.departments.insert_one({
            "code": code,
            "name": dept_names[code],
            "created_at": datetime.utcnow()
        }).inserted_id
    print("Seeded Departments.")

    # 3. Seed Courses
    course_ids = {}
    for code, dept_id in dept_ids.items():
        course_ids[code] = mongo_client.db.courses.insert_one({
            "name": f"B.Tech {code}",
            "code": f"BTECH-{code.replace(' ', '')}",
            "department_id": dept_id,
            "duration": "4 Years",
            "regulation": "R2026",
            "total_semesters": 8,
            "created_at": datetime.utcnow()
        }).inserted_id
    print("Seeded Courses.")

    # 4. Generate Object IDs for Users
    admin_id = ObjectId()
    principal_id = ObjectId()
    hod_cs_id = ObjectId()
    hod_math_id = ObjectId()  # AIML HOD
    
    faculty_ids = [ObjectId() for _ in range(6)]
    student_ids = [ObjectId() for _ in range(13)]

    # 5. Seed Classes
    # PIT-CSE-Y2 (CSE Year 2) & PIT-AIML-Y2 (AIML Year 2)
    class_cs_id = mongo_client.db.classes.insert_one({
        "name": "CSE Year 2 Section A",
        "code": "PIT-CSE-Y2-A",
        "course_id": course_ids["CSE"],
        "department_id": dept_ids["CSE"],
        "faculty_id": hod_cs_id, # HOD acts as mentor
        "academic_year": "2026-2027",
        "semester": 4,
        "section": "A"
    }).inserted_id

    class_aiml_id = mongo_client.db.classes.insert_one({
        "name": "AIML Year 2 Section A",
        "code": "PIT-AIML-Y2-A",
        "course_id": course_ids["AIML"],
        "department_id": dept_ids["AIML"],
        "faculty_id": hod_math_id,
        "academic_year": "2026-2027",
        "semester": 4,
        "section": "A"
    }).inserted_id
    print("Seeded Classes.")

    # 6. Seed Subjects
    subjects = [
        {"name": "Database Management Systems", "code": "CS201", "department_id": dept_ids["CSE"], "credits": 4, "type": "Theory"},
        {"name": "Operating Systems", "code": "CS202", "department_id": dept_ids["CSE"], "credits": 4, "type": "Theory"},
        {"name": "Computer Networks", "code": "CS203", "department_id": dept_ids["CSE"], "credits": 3, "type": "Theory"},
        {"name": "DBMS Laboratory", "code": "CS204", "department_id": dept_ids["CSE"], "credits": 2, "type": "Laboratory"},
        {"name": "Machine Learning", "code": "AM201", "department_id": dept_ids["AIML"], "credits": 4, "type": "Theory"},
        {"name": "Deep Learning", "code": "AM202", "department_id": dept_ids["AIML"], "credits": 4, "type": "Theory"},
        {"name": "Probability & Statistics", "code": "AM203", "department_id": dept_ids["AIML"], "credits": 3, "type": "Theory"}
    ]
    mongo_client.db.subjects.insert_many(subjects)
    print("Seeded Subjects.")

    # 7. Seed Users (Unified Collection)
    users_data = []

    # Admin User
    users_data.append({
        "_id": admin_id,
        "user_id": "PIT-ADM-01",
        "role": "admin",
        "name": "Super Admin",
        "first_name": "Super",
        "last_name": "Admin",
        "email": "admin@college.edu",
        "phone": "+91-9876543210",
        "password_hash": hashed_password,
        "profile_picture": "https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?q=80&w=256",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    # Principal User
    users_data.append({
        "_id": principal_id,
        "user_id": "PIT-PRN-01",
        "role": "admin", # elevated permissions
        "designation": "Principal",
        "name": "Dr. Skinner",
        "first_name": "Dr.",
        "last_name": "Skinner",
        "email": "principal@college.edu",
        "phone": "+91-9876543211",
        "password_hash": hashed_password,
        "profile_picture": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?q=80&w=256",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    # HOD CS
    users_data.append({
        "_id": hod_cs_id,
        "user_id": "PIT-HOD-CSE",
        "role": "hod",
        "designation": "Head of Department - CSE",
        "name": "Dr. Alan Turing",
        "first_name": "Alan",
        "last_name": "Turing",
        "email": "hod.cs@college.edu",
        "phone": "+91-9876543212",
        "password_hash": hashed_password,
        "profile_picture": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=256",
        "is_active": True,
        "department_id": dept_ids["CSE"],
        "qualification": "Ph.D. in Theory of Computation",
        "experience_years": 15,
        "specialization": ["Computation", "Cryptography", "AI"],
        "joining_date": "2020-06-01",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    # HOD AIML
    users_data.append({
        "_id": hod_math_id,
        "user_id": "PIT-HOD-AIML",
        "role": "hod",
        "designation": "Head of Department - AIML",
        "name": "Dr. John Nash",
        "first_name": "John",
        "last_name": "Nash",
        "email": "hod.math@college.edu",
        "phone": "+91-9876543213",
        "password_hash": hashed_password,
        "profile_picture": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=256",
        "is_active": True,
        "department_id": dept_ids["AIML"],
        "qualification": "Ph.D. in Game Theory & Optimization",
        "experience_years": 18,
        "specialization": ["Game Theory", "Optimization", "Neural Networks"],
        "joining_date": "2019-01-15",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })

    # Faculty members
    for i, fid in enumerate(faculty_ids):
        dept_code = "CSE" if i < 3 else "AIML"
        users_data.append({
            "_id": fid,
            "user_id": f"PIT-FAC-{i:03d}",
            "role": "faculty",
            "designation": "Assistant Professor",
            "name": f"Faculty {i}",
            "first_name": "Faculty",
            "last_name": str(i),
            "email": f"faculty{i}@college.edu",
            "phone": f"+91-98765433{i:02d}",
            "password_hash": hashed_password,
            "profile_picture": f"https://images.unsplash.com/photo-1494790108377-be9c29b29330?q=80&w=256",
            "is_active": True,
            "department_id": dept_ids[dept_code],
            "qualification": "M.Tech / Ph.D.",
            "experience_years": 5 + i,
            "specialization": ["Database Systems", "Compiler Design"] if dept_code == "CSE" else ["Deep Learning", "Statistics"],
            "joining_date": "2022-08-01",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

    # Students (Ram Kumar is student0, at-risk student)
    student_names = [
        ("Ram", "Kumar"), ("Priya", "Sharma"), ("Aarav", "Patel"), ("Sneha", "Reddy"), ("Karthik", "Raja"),
        ("Ananya", "Sen"), ("Rahul", "Varma"), ("Diya", "Nair"), ("Kabir", "Singh"), ("Meera", "Joshi"),
        ("Vikram", "Rao"), ("Tara", "Das"), ("Aswin", "Kumar")
    ]
    
    for i, sid in enumerate(student_ids):
        first_name, last_name = student_names[i]
        dept_code = "CSE" if i < 6 else "AIML"
        class_id = class_cs_id if i < 6 else class_aiml_id
        
        # Ram Kumar is setup as a critical at-risk day scholar
        # student1 (Priya) is set up as a hosteller
        student_type = "day_scholar" if i % 2 == 0 else "hosteller"
        
        student_doc = {
            "_id": sid,
            "user_id": f"PIT-STU-2023-{i:03d}",
            "role": "student",
            "name": f"{first_name} {last_name}",
            "first_name": first_name,
            "last_name": last_name,
            "email": f"student{i}@college.edu",
            "phone": f"+91-98765444{i:02d}",
            "password_hash": hashed_password,
            "profile_picture": f"https://images.unsplash.com/photo-{1530000000000 + i*1000000}?q=80&w=256" if i != 0 else "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?q=80&w=256",
            "is_active": True,
            "department_id": dept_ids[dept_code],
            "class_id": class_id,
            "course": f"B.Tech {dept_code}",
            "current_semester": 4,
            "section": "A",
            "roll_number": f"23{dept_code}0{i+1:02d}",
            "admission_number": f"ADM23{dept_code}{i+1:02d}",
            "batch": "2023-2027",
            "cgpa": 6.8 if i == 0 else round(random.uniform(7.5, 9.5), 2),
            "sgpa": 6.5 if i == 0 else round(random.uniform(7.5, 9.5), 2),
            "arrears_count": 0,
            "student_type": student_type,
            "mentor_id": hod_cs_id if dept_code == "CSE" else hod_math_id,
            "admission_date": "2023-08-20",
            
            # Personal details
            "dob": "2005-04-12",
            "age": 21,
            "gender": "Male" if i % 2 == 0 else "Female",
            "address": "45 Gandhi Road, Tech City",
            "emergency_contact": "Parent: +91-9988776655",
            
            # Skills & Career
            "technical_skills": ["Python", "C++", "HTML/CSS"] if dept_code == "CSE" else ["Python", "SQL", "Pandas"],
            "programming_languages": ["Python", "Java", "C++"],
            "soft_skills": ["Communication", "Teamwork"],
            "projects": [{"title": "Campus ERP Portal", "description": "Full stack university automation website"}],
            "placement_status": "unplaced",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        if student_type == "hosteller":
            student_doc.update({
                "hostel_id": "Tech Campus Residence",
                "block": "Block C",
                "room_number": f"{100 + i}",
                "bed_number": "A",
                "hostel_status": "Active",
                "mess_info": "North Indian Mess B",
                "hostel_attendance": "94%"
            })
        else: # day_scholar
            student_doc.update({
                "bus_number": "PIT-BUS-12",
                "route_id": "Route 4B",
                "pickup_point": "Guindy Metro Station",
                "driver_name": "Ramesh Kumar",
                "driver_phone": "+91-9441234567",
                "route_timing": "07:45 AM",
                "transport_status": "Active"
            })
            
        users_data.append(student_doc)

    mongo_client.db.users.insert_many(users_data)
    print("Seeded Users collection.")

    # 8. Seed Timetable
    mongo_client.db.timetables.insert_one({
        "class_id": class_cs_id,
        "schedule": "Monday to Friday: 08:30 AM - 03:30 PM",
        "periods": [
            {"day": "Monday", "period_1": "CS201", "period_2": "CS202", "period_3": "CS203", "period_4": "CS204"},
            {"day": "Tuesday", "period_1": "CS202", "period_2": "CS203", "period_3": "CS201", "period_4": "CS204"}
        ]
    })
    mongo_client.db.timetables.insert_one({
        "class_id": class_aiml_id,
        "schedule": "Monday to Friday: 08:30 AM - 03:30 PM",
        "periods": [
            {"day": "Monday", "period_1": "AM201", "period_2": "AM202", "period_3": "AM203", "period_4": "Self Study"},
            {"day": "Tuesday", "period_1": "AM202", "period_2": "AM203", "period_3": "AM201", "period_4": "Library"}
        ]
    })
    print("Seeded Timetables.")

    # 9. Seed Attendance Records
    # For student0 (Ram Kumar), we want an at-risk low attendance pattern (e.g. 11 present, 9 absent -> 55%)
    # For others, we want high attendance (e.g. 18 present, 2 absent -> 90%)
    for i, sid in enumerate(student_ids):
        class_id = class_cs_id if i < 6 else class_aiml_id
        is_at_risk = (i == 0)
        
        for day in range(20):
            date_str = (datetime.now() - timedelta(days=day)).strftime("%Y-%m-%d")
            status = "absent" if is_at_risk and day % 2 == 0 else "present" if not is_at_risk and day > 2 else "absent"
            
            mongo_client.db.attendance.insert_one({
                "student_id": sid,
                "class_id": class_id,
                "subject_code": "CS201" if i < 6 else "AM201",
                "date": date_str,
                "status": status,
                "created_at": datetime.utcnow()
            })
    print("Seeded Attendance.")

    # 10. Seed Results
    # Ram Kumar (student0) has score drop (78 -> 64 -> 55) in recent CSE assessments
    # Others have normal high grades
    for i, sid in enumerate(student_ids):
        is_at_risk = (i == 0)
        subj = "CS201" if i < 6 else "AM201"
        
        if is_at_risk:
            # 3 exam records showing decline
            mongo_client.db.results.insert_one({"student_id": sid, "exam_id": "EXM_001", "exam_name": "Unit Test 1", "subject_code": subj, "score": 78, "grade": "B", "date": "2026-07-10"})
            mongo_client.db.results.insert_one({"student_id": sid, "exam_id": "EXM_002", "exam_name": "Internal Assessment 1", "subject_code": subj, "score": 64, "grade": "C", "date": "2026-07-25"})
            mongo_client.db.results.insert_one({"student_id": sid, "exam_id": "EXM_003", "exam_name": "Model Exam", "subject_code": subj, "score": 55, "grade": "D", "date": "2026-08-10"})
        else:
            mongo_client.db.results.insert_one({"student_id": sid, "exam_id": "EXM_001", "exam_name": "Unit Test 1", "subject_code": subj, "score": random.randint(70, 95), "grade": "A", "date": "2026-07-10"})
            mongo_client.db.results.insert_one({"student_id": sid, "exam_id": "EXM_002", "exam_name": "Internal Assessment 1", "subject_code": subj, "score": random.randint(72, 98), "grade": "A", "date": "2026-07-25"})
    print("Seeded Results.")

    # 11. Seed Assignments & Submissions
    for cls_id in [class_cs_id, class_aiml_id]:
        asg_id = mongo_client.db.assignments.insert_one({
            "class_id": cls_id,
            "title": "Homework 1 - Core Foundations",
            "subject_code": "CS201" if cls_id == class_cs_id else "AM201",
            "due_date": "2026-08-15"
        }).inserted_id

        students_in_class = mongo_client.db.users.find({"role": "student", "class_id": cls_id})
        for s in students_in_class:
            sid = s["_id"]
            # student0 (Ram) has missed submission or late submission
            if s["user_id"] == "PIT-STU-2023-000":
                mongo_client.db.submissions.insert_one({
                    "assignment_id": asg_id,
                    "student_id": sid,
                    "title": "Homework 1 - Core Foundations",
                    "status": "pending",
                    "due_date": "2026-08-15",
                    "is_late": True
                })
            else:
                mongo_client.db.submissions.insert_one({
                    "assignment_id": asg_id,
                    "student_id": sid,
                    "title": "Homework 1 - Core Foundations",
                    "status": "graded",
                    "due_date": "2026-08-15",
                    "score": random.randint(75, 100),
                    "is_late": False
                })
    print("Seeded Assignments and Submissions.")

    # 12. Seed Interventions
    # Ram Kumar (student0) has an active intervention plan initiated by Turing (hod_cs_id)
    mongo_client.db.interventions.insert_one({
        "intervention_id": "ITV_001",
        "student_id": str(student_ids[0]),
        "student_name": "Ram Kumar",
        "faculty_id": str(hod_cs_id),
        "faculty_name": "Dr. Alan Turing",
        "course_name": "B.Tech Computer Science & Engineering",
        "priority_tier": "Immediate Attention Needed",
        "action_code": "CRITICAL",
        "status": "In Progress",
        "created_at": "2026-08-10",
        "evaluation_due": "2026-08-24",
        "key_signals": {
            "attendance": "55.0% (Declining)",
            "exam_trend": "Average 65.7/100 (2 consecutive drops)",
            "assignment_rate": "0% Completion (1 delayed/missed)"
        },
        "suggested_action": "Schedule 1-on-1 concept mentoring session, provide homework catch-up worksheets, and contact parent.",
        "teacher_notes": "First mentoring scheduled for tomorrow.",
        "faculty_notes": "First mentoring scheduled for tomorrow.",
        "outcome_metrics": {
            "initial_attendance": 55.0,
            "current_attendance": 70.0,
            "initial_grade_avg": 65.7,
            "current_grade_avg": 72.0,
            "improvement_status": "Positive Progress (+15% Attendance)"
        }
    })
    
    # SNR Priya has resolved intervention
    mongo_client.db.interventions.insert_one({
        "intervention_id": "ITV_002",
        "student_id": str(student_ids[1]),
        "student_name": "Priya Sharma",
        "faculty_id": str(hod_cs_id),
        "faculty_name": "Dr. Alan Turing",
        "course_name": "B.Tech Computer Science & Engineering",
        "priority_tier": "Support Recommended",
        "action_code": "NEEDS_ATTENTION",
        "status": "Resolved",
        "created_at": "2026-08-01",
        "evaluation_due": "2026-08-15",
        "key_signals": {
            "attendance": "72.0% (Stable)",
            "exam_trend": "Average 78.0/100",
            "assignment_rate": "80% Completion"
        },
        "suggested_action": "Targeted concept review & regular follow up.",
        "teacher_notes": "Student showed excellent improvement, attendance is now 88%.",
        "faculty_notes": "Student showed excellent improvement, attendance is now 88%.",
        "outcome_metrics": {
            "initial_attendance": 72.0,
            "current_attendance": 88.0,
            "initial_grade_avg": 78.0,
            "current_grade_avg": 82.0,
            "improvement_status": "Resolved"
        }
    })
    print("Seeded Interventions.")

    # 13. Seed Notices and Announcements
    mongo_client.db.notices.insert_many([
        {
            "title": "Independence Day Holiday",
            "content": "PIT will remain closed on 15th August 2026 in observance of Independence Day.",
            "visibility": ["student", "faculty", "hod"],
            "createdAt": datetime.utcnow()
        },
        {
            "title": "Semester Registration Deadline",
            "content": "All students must register their elective choices for Semester 4 by 22nd August 2026.",
            "visibility": ["student"],
            "createdAt": datetime.utcnow()
        }
    ])
    print("Seeded Notices.")

    # 14. Seed Events
    mongo_client.db.events.insert_many([
        {
            "title": "PIT Hackathon 2026",
            "description": "Annual 24-hour campus hackathon on Agentic AI and Cloud Architectures.",
            "date": "2026-09-05",
            "department_id": dept_ids["CSE"],
            "visibility": ["student", "faculty"]
        },
        {
            "title": "Guest Lecture on Deep Learning",
            "description": "Dr. Geoffrey Hinton's virtual lecture on feed-forward networks.",
            "date": "2026-08-20",
            "department_id": dept_ids["AIML"],
            "visibility": ["student", "faculty"]
        }
    ])
    print("Seeded Events.")

    # 15. Seed student requests
    mongo_client.db.studentRequests.insert_one({
        "student_id": student_ids[0],
        "request_type": "Leave Request",
        "details": "Requesting 2 days leave for family emergency on 24-25 August.",
        "status": "Pending",
        "created_at": datetime.utcnow()
    })
    print("Seeded student requests.")

    # 16. Seed academic insights
    for sid in student_ids:
        mongo_client.db.academicInsights.insert_one({
            "student_id": sid,
            "insight": "Student is on track. Maintain standard course participation.",
            "created_at": datetime.utcnow()
        })
    print("Seeded Academic Insights.")

    print("Database seeded successfully with PIT single-institution details!")

if __name__ == "__main__":
    seed_database()
