import os
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pymongo
from bson import ObjectId
from app.core.config import settings

class MongoDBClient:
    """
    PORTALITICS MongoDB Client
    """
    def __init__(self):
        self.uri = settings.MONGODB_URI
        self.db_name = settings.MONGODB_DB_NAME
        self._connected = False
        self._mocked = False
        
        try:
            # Short timeout so we don't hang if Mongo isn't running
            self.client = pymongo.MongoClient(self.uri, serverSelectionTimeoutMS=2000)
            self.db = self.client[self.db_name]
            self.client.server_info()
            self._connected = True
            print("[INFO] Successfully connected to MongoDB.")
        except Exception as e:
            print(f"[WARNING] MongoDB connection failed: {e}. Falling back to in-memory mongomock client.")
            print("==========================================================================")
            print(" [WARNING] PORTALITICS RUNNING IN DEMO-MODE WITH IN-MEMORY MONGOMOCK DB")
            print(" Data written during this execution will NOT persist after process exit!")
            print("==========================================================================")
            import mongomock
            self.client = mongomock.MongoClient()
            self.db = self.client[self.db_name]
            self._connected = True
            self._mocked = True
            
        self.create_indexes()
        
        # Auto-seed if running in mocked state so the app has data on startup
        if self._mocked:
            self.auto_seed()

    def is_connected(self) -> bool:
        if self._mocked:
            return True
        try:
            self.client.server_info()
            self._connected = True
            return True
        except:
            self._connected = False
            return False

    def create_indexes(self):
        self.db.users.create_index("email", unique=True)
        self.db.users.create_index("role")
        self.db.departments.create_index("code", unique=True)
        self.db.courses.create_index("code", unique=True)
        self.db.subjects.create_index("code", unique=True)
        self.db.classes.create_index("code", unique=True)
        self.db.attendance.create_index([("student_id", 1), ("class_id", 1), ("date", 1)])
        self.db.interventions.create_index("student_id")
        self.db.interventions.create_index("faculty_id")

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        uid = ObjectId(user_id) if isinstance(user_id, str) and len(user_id) == 24 else user_id
        user = self.db.users.find_one({"_id": uid})
        if user:
            user["id"] = str(user["_id"])
        return user

    def get_all_students(self) -> List[Dict[str, Any]]:
        students = list(self.db.users.find({"role": "student"}))
        for s in students:
            s["id"] = str(s["_id"])
        return students

    def get_all_departments(self) -> List[Dict[str, Any]]:
        departments = list(self.db.departments.find({}))
        for d in departments:
            d["id"] = str(d["_id"])
        return departments

    def find_departments(self, query: str = "") -> List[Dict[str, Any]]:
        if not query:
            return self.get_all_departments()
        regex = {"$regex": query, "$options": "i"}
        departments = list(self.db.departments.find({"$or": [{"code": regex}, {"name": regex}] }))
        for d in departments:
            d["id"] = str(d["_id"])
        return departments

    def get_timetables(self) -> List[Dict[str, Any]]:
        timetables = list(self.db.timetables.find({}))
        for t in timetables:
            t["id"] = str(t["_id"])
        return timetables

    def get_student_academic_history(self, student_id: str) -> Dict[str, Any]:
        uid = ObjectId(student_id) if isinstance(student_id, str) and len(student_id) == 24 else student_id
        
        # 1. Fetch attendance records
        attendance = list(self.db.attendance.find({"student_id": uid}))
        
        # 2. Fetch results
        results = list(self.db.results.find({"student_id": uid}))
        
        # 3. Fetch submissions (assignments)
        submissions = list(self.db.submissions.find({"student_id": uid}))
        
        return {
            "attendance": attendance,
            "exams": [
                {
                    "subject": r.get("subject_code", "General"),
                    "score": float(r.get("score", 0)),
                    "exam_name": r.get("exam_name", "Test")
                }
                for r in results
            ],
            "assignments": [
                {
                    "title": s.get("title", "Assignment"),
                    "status": s.get("status", "submitted"),
                    "due_date": s.get("due_date", "2026-08-20"),
                    "is_late": s.get("is_late", False)
                }
                for s in submissions
            ]
        }

    def record_attendance(self, student_id: str, subject_code: str, status: str):
        uid = ObjectId(student_id) if isinstance(student_id, str) and len(student_id) == 24 else student_id
        user = self.db.users.find_one({"_id": uid})
        class_id = user.get("class_id") if user else None
        
        doc = {
            "student_id": uid,
            "class_id": class_id,
            "subject_code": subject_code,
            "status": status,  # present, absent, late
            "date": datetime.now().strftime("%Y-%m-%d"),
            "created_at": datetime.utcnow()
        }
        self.db.attendance.insert_one(doc)

    def create_assignment(self, assignment_data: Dict[str, Any]):
        assignment_data["created_at"] = datetime.utcnow()
        self.db.assignments.insert_one(assignment_data)

    def get_all_assignments(self) -> List[Dict[str, Any]]:
        assignments = list(self.db.assignments.find({}))
        for a in assignments:
            a["id"] = str(a["_id"])
        return assignments

    def get_all_exams(self) -> List[Dict[str, Any]]:
        exams = list(self.db.exams.find({}))
        for e in exams:
            e["id"] = str(e["_id"])
        return exams

    def record_exam_mark(self, student_id: str, exam_id: str, exam_name: str, subject: str, score: float):
        uid = ObjectId(student_id) if isinstance(student_id, str) and len(student_id) == 24 else student_id
        grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "F"
        update_doc = {
            "$set": {
                "student_id": uid,
                "exam_id": exam_id,
                "exam_name": exam_name,
                "subject_code": subject,
                "score": score,
                "grade": grade,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "updated_at": datetime.utcnow()
            },
            "$setOnInsert": {
                "created_at": datetime.utcnow()
            }
        }
        self.db.results.update_one(
            {"student_id": uid, "subject_code": subject, "exam_name": exam_name},
            update_doc,
            upsert=True
        )

    def get_faculty_support_queue(self, faculty_id: str) -> List[Dict[str, Any]]:
        fid = ObjectId(faculty_id) if isinstance(faculty_id, str) and len(faculty_id) == 24 else faculty_id
        interventions = list(self.db.interventions.find({"faculty_id": fid}))
        for i in interventions:
            i["id"] = str(i["_id"])
        return interventions

    def get_all_interventions(self) -> List[Dict[str, Any]]:
        interventions = list(self.db.interventions.find({}))
        for i in interventions:
            i["id"] = str(i["_id"])
        return interventions

    def get_intervention_by_id(self, intervention_id: str) -> Optional[Dict[str, Any]]:
        query = {}
        if isinstance(intervention_id, str) and len(intervention_id) == 24:
            query = {"$or": [{"_id": ObjectId(intervention_id)}, {"intervention_id": intervention_id}]}
        else:
            query = {"intervention_id": intervention_id}
        doc = self.db.interventions.find_one(query)
        if doc:
            doc["id"] = str(doc["_id"])
        return doc

    def initiate_intervention(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        doc["created_at"] = doc.get("created_at") or datetime.now().strftime("%Y-%m-%d")
        doc["updated_at"] = datetime.utcnow()
        res = self.db.interventions.insert_one(doc)
        doc["_id"] = res.inserted_id
        doc["id"] = str(res.inserted_id)
        return doc

    def update_intervention_status(self, intervention_id: str, status: str, notes: str) -> Optional[Dict[str, Any]]:
        """
        Updates the monitoring status and log notes for an active student intervention.
        """
        query = {}
        if isinstance(intervention_id, str) and len(intervention_id) == 24:
            query = {"$or": [{"_id": ObjectId(intervention_id)}, {"intervention_id": intervention_id}]}
        else:
            query = {"intervention_id": intervention_id}
            
        self.db.interventions.update_one(
            query,
            {"$set": {"status": status, "teacher_notes": notes, "faculty_notes": notes, "updated_at": datetime.utcnow()}}
        )
        return self.get_intervention_by_id(intervention_id)

    def calculate_institution_outcomes(self) -> Dict[str, Any]:
        """
        Aggregates intervention totals, resolution states, and computes institutional success rates.
        """
        resolved_count = self.db.interventions.count_documents({"status": "Resolved"})
        in_progress_count = self.db.interventions.count_documents({"status": "In Progress"})
        escalated_count = self.db.interventions.count_documents({"status": "Escalated"})
        total_count = resolved_count + in_progress_count + escalated_count
        success_rate = round((resolved_count / total_count) * 100, 1) if total_count > 0 else 100.0
        return {
            "resolved_count": resolved_count,
            "in_progress_count": in_progress_count,
            "escalated_count": escalated_count,
            "total_count": total_count,
            "overall_success_rate": success_rate
        }

    def register_user(self, name: str, email: str, role: str, department_name: str = "") -> Dict[str, Any]:
        """
        Utility method to register a user document primarily used for isolation test seeding.
        """
        # Compatibility method for tests
        user_data = {
            "name": name,
            "email": email,
            "role": role,
            "department_name": department_name,
            "is_active": True,
            "password_hash": "$2b$12$T5q3Z2Jk7b/1U3W7w7b9AeC2Qh4QxP/eO2m/Fp7z99x9p9s9s9s9s", # dummy hash
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        res = self.db.users.insert_one(user_data)
        user_data["id"] = str(res.inserted_id)
        user_data["_id"] = res.inserted_id
        return user_data

    def create_user_transaction(self, user_data: Dict[str, Any], password: str, department: str = "") -> Dict[str, Any]:
        from app.core.security import hash_password
        user_data["password_hash"] = hash_password(password)
        if department:
            user_data["department_id"] = department
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        res = self.db.users.insert_one(user_data)
        user_data["_id"] = res.inserted_id
        user_data["id"] = str(res.inserted_id)
        return user_data

    def get_admin_dashboard_data(self) -> Dict[str, Any]:
        students_count = self.db.users.count_documents({"role": "student"})
        faculty_count = self.db.users.count_documents({"role": "faculty"})
        departments_count = self.db.departments.count_documents({})
        courses_count = self.db.courses.count_documents({})
        
        students = list(self.db.users.find({"role": "student"}))
        for s in students:
            s["id"] = str(s["_id"])
            
        faculty = list(self.db.users.find({"role": {"$in": ["faculty", "hod"]}}))
        for f in faculty:
            f["id"] = str(f["_id"])
            
        classes = list(self.db.classes.find({}))
        for c in classes:
            c["id"] = str(c["_id"])
            
        courses = list(self.db.courses.find({}))
        for c in courses:
            c["id"] = str(c["_id"])
            
        results = list(self.db.results.find({}))
        for r in results:
            r["id"] = str(r["_id"])
            
        assignments = list(self.db.assignments.find({}))
        for a in assignments:
            a["id"] = str(a["_id"])
            
        interventions = list(self.db.interventions.find({}))
        for i in interventions:
            i["id"] = str(i["_id"])
            
        return {
            "students_count": students_count,
            "faculty_count": faculty_count,
            "departments_count": departments_count,
            "courses_count": courses_count,
            "active_users": students_count + faculty_count,
            "system_metrics": {"cpu": "12%", "memory": "2.4GB"},
            "students": students,
            "faculty": faculty,
            "classes": classes,
            "courses": courses,
            "results": results,
            "assignments": assignments,
            "interventions": interventions
        }

    def get_student_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        uid = ObjectId(user_id) if isinstance(user_id, str) and len(user_id) == 24 else user_id
        
        user = self.db.users.find_one({"_id": uid}, {"password_hash": 0})
        if user:
            user["id"] = str(user["_id"])
            user["avatar"] = user.get("profile_picture") or "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=256"
            user["program_name"] = user.get("course") or "B.Tech Computer Science & Engineering"
            user["semester"] = user.get("current_semester") or 4
            user["section"] = user.get("section") or "A"
            user["roll_number"] = user.get("roll_number") or "PIT-CSE-023"
            user["cgpa"] = user.get("cgpa") or 8.4
            user["name"] = user.get("name") or "Student"
            
        class_id = user.get("class_id") if user else None
        classes = list(self.db.classes.find({"_id": class_id})) if class_id else []
        for c in classes:
            c["id"] = str(c["_id"])
            
        timetable = list(self.db.timetables.find({"class_id": class_id})) if class_id else []
        attendance = list(self.db.attendance.find({"student_id": uid}))
        assignments = list(self.db.assignments.find({"class_id": class_id})) if class_id else []
        results = list(self.db.results.find({"student_id": uid}))
        insights = list(self.db.academicInsights.find({"student_id": uid}))
        
        # Cross-reference student submissions
        submissions = list(self.db.submissions.find({"student_id": uid}))
        sub_map = {str(sub.get("assignment_id")): sub for sub in submissions}
        
        for a in assignments:
            a["id"] = str(a["_id"])
            sub = sub_map.get(str(a["_id"]))
            if sub:
                a["status"] = sub.get("status", "submitted")
                a["score"] = sub.get("score")
                a["is_late"] = sub.get("is_late", False)
            else:
                a["status"] = "pending"
                a["score"] = None
                a["is_late"] = False
        
        return {
            "user": user,
            "classes": classes,
            "timetable": timetable,
            "attendance": attendance,
            "assignments": assignments,
            "results": results,
            "insights": insights
        }

    def get_faculty_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        uid = ObjectId(user_id) if isinstance(user_id, str) and len(user_id) == 24 else user_id
        
        user = self.db.users.find_one({"_id": uid}, {"password_hash": 0})
        if user:
            user["id"] = str(user["_id"])
            user["name"] = user.get("name", "Faculty")
            user["avatar"] = user.get("profile_picture") or "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?q=80&w=256"
            
        # Assigned classes
        assigned_classes = list(self.db.classes.find({"faculty_id": uid}))
        class_ids = [c["_id"] for c in assigned_classes]
        
        for c in assigned_classes:
            c["id"] = str(c["_id"])
            
        # Enrolled students (all students belonging to these classes)
        students = list(self.db.users.find({"role": "student", "class_id": {"$in": class_ids}}))
        for s in students:
            s["id"] = str(s["_id"])
            
        attendance = list(self.db.attendance.find({"class_id": {"$in": class_ids}}))
        tasks = list(self.db.facultyTasks.find({"faculty_id": uid}))
        assignments = list(self.db.assignments.find({"class_id": {"$in": class_ids}}))
        
        # Intervention queue for this faculty
        intervention_queue = list(self.db.interventions.find({"faculty_id": uid}))
        for i in intervention_queue:
            i["id"] = str(i["_id"])
            
        return {
            "user": user,
            "classes": assigned_classes,
            "students": students,
            "student_counts": len(students),
            "average_attendance": 85.5,
            "tasks": tasks,
            "assignments": assignments,
            "intervention_queue": intervention_queue
        }

    def get_hod_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        uid = ObjectId(user_id) if isinstance(user_id, str) and len(user_id) == 24 else user_id
        
        user = self.db.users.find_one({"_id": uid}, {"password_hash": 0})
        if user:
            user["id"] = str(user["_id"])
            user["name"] = user.get("name", "HOD")
            
        dept_id = user.get("department_id") if user else None
        department = self.db.departments.find_one({"_id": ObjectId(dept_id)}) if dept_id else None
        
        faculty = []
        students = []
        if dept_id:
            faculty = list(self.db.users.find({"role": "faculty", "department_id": dept_id}))
            for f in faculty:
                f["id"] = str(f["_id"])
            students = list(self.db.users.find({"role": "student", "department_id": dept_id}))
            for s in students:
                s["id"] = str(s["_id"])
                
        # Interventions in this department
        interventions = list(self.db.interventions.find({"department_id": dept_id})) if dept_id else []
        for i in interventions:
            i["id"] = str(i["_id"])
            
        return {
            "user": user,
            "department": department,
            "faculty": faculty,
            "students": students,
            "intervention_queue": interventions,
            "metrics": {
                "total_students": len(students),
                "total_faculty": len(faculty),
                "active_interventions": len([i for i in interventions if i.get("status") == "In Progress"])
            }
        }

    def get_principal_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        total_students = self.db.users.count_documents({"role": "student"})
        total_faculty = self.db.users.count_documents({"role": "faculty"})
        total_departments = self.db.departments.count_documents({})
        total_courses = self.db.courses.count_documents({})
        
        outcomes = self.calculate_institution_outcomes()
        
        return {
            "total_students": total_students,
            "total_faculty": total_faculty,
            "total_departments": total_departments,
            "total_courses": total_courses,
            "resolved_interventions": outcomes["resolved_count"],
            "active_interventions": outcomes["in_progress_count"],
            "success_rate": outcomes["overall_success_rate"],
            "system_status": {"cpu": "22%", "memory": "1.8GB"}
        }

    def auto_seed(self):
        print("[INFO] Starting auto-seeding of in-memory mongomock database...")
        # Clear collections
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
            self.db[col].delete_many({})

        hashed_password = "$2b$12$KMOVMrYC.1YS0a11RmIsA.qI1mI3dYK35IoN33Et5JnHObE3Cz.fq" # precomputed bcrypt hash of password123

        # 1. Institution
        institution = {
            "name": "Portalitics Institute of Technology",
            "code": "PIT",
            "address": "123 Education Boulevard, Tech City, 600097",
            "academic_year": "2026-2027",
            "contact": {
                "email": "info@pit.edu",
                "phone": "+91-44-24501234"
            },
            "principal": {
                "name": "Dr. Skinner",
                "email": "principal@college.edu"
            }
        }
        self.db.institution.insert_one(institution)

        # 2. Departments
        dept_codes = ["AIML", "AIDS", "CSE", "Cyber Security", "ECE", "EEE", "MECH", "IT"]
        dept_ids = {}
        for code in dept_codes:
            dept_ids[code] = self.db.departments.insert_one({
                "code": code,
                "name": f"Department of {code}",
                "created_at": datetime.utcnow()
            }).inserted_id

        # 3. Courses
        course_ids = {}
        for code, dept_id in dept_ids.items():
            course_ids[code] = self.db.courses.insert_one({
                "name": f"B.Tech {code}",
                "code": f"BTECH-{code.replace(' ', '')}",
                "department_id": dept_id,
                "duration": "4 Years",
                "regulation": "R2026",
                "total_semesters": 8
            }).inserted_id

        # 4. IDs
        admin_id = ObjectId()
        principal_id = ObjectId()
        hod_cs_id = ObjectId()
        hod_math_id = ObjectId()
        faculty_ids = [ObjectId() for _ in range(6)]
        student_ids = [ObjectId() for _ in range(13)]

        # 5. Classes
        class_cs_id = self.db.classes.insert_one({
            "name": "CSE Year 2 Section A",
            "code": "PIT-CSE-Y2-A",
            "course_id": course_ids["CSE"],
            "department_id": dept_ids["CSE"],
            "faculty_id": hod_cs_id,
            "academic_year": "2026-2027",
            "semester": 4,
            "section": "A"
        }).inserted_id

        class_aiml_id = self.db.classes.insert_one({
            "name": "AIML Year 2 Section A",
            "code": "PIT-AIML-Y2-A",
            "course_id": course_ids["AIML"],
            "department_id": dept_ids["AIML"],
            "faculty_id": hod_math_id,
            "academic_year": "2026-2027",
            "semester": 4,
            "section": "A"
        }).inserted_id

        # 6. Subjects
        subjects = [
            {"name": "Database Management Systems", "code": "CS201", "department_id": dept_ids["CSE"], "credits": 4, "type": "Theory"},
            {"name": "Operating Systems", "code": "CS202", "department_id": dept_ids["CSE"], "credits": 4, "type": "Theory"},
            {"name": "Machine Learning", "code": "AM201", "department_id": dept_ids["AIML"], "credits": 4, "type": "Theory"}
        ]
        self.db.subjects.insert_many(subjects)

        # 7. Users
        users = [
            {
                "_id": admin_id,
                "user_id": "PIT-ADM-01",
                "role": "admin",
                "name": "Super Admin",
                "email": "admin@college.edu",
                "password_hash": hashed_password,
                "is_active": True
            },
            {
                "_id": principal_id,
                "user_id": "PIT-PRN-01",
                "role": "admin",
                "designation": "Principal",
                "name": "Dr. Skinner",
                "email": "principal@college.edu",
                "password_hash": hashed_password,
                "is_active": True
            },
            {
                "_id": hod_cs_id,
                "user_id": "PIT-HOD-CSE",
                "role": "hod",
                "designation": "Head of Department - CSE",
                "name": "Dr. Alan Turing",
                "email": "hod.cs@college.edu",
                "password_hash": hashed_password,
                "is_active": True,
                "department_id": dept_ids["CSE"]
            },
            {
                "_id": hod_math_id,
                "user_id": "PIT-HOD-AIML",
                "role": "hod",
                "designation": "Head of Department - AIML",
                "name": "Dr. John Nash",
                "email": "hod.math@college.edu",
                "password_hash": hashed_password,
                "is_active": True,
                "department_id": dept_ids["AIML"]
            }
        ]

        # Faculty
        for i, fid in enumerate(faculty_ids):
            dept_code = "CSE" if i < 3 else "AIML"
            users.append({
                "_id": fid,
                "user_id": f"PIT-FAC-{i:03d}",
                "role": "faculty",
                "name": f"Faculty {i}",
                "email": f"faculty{i}@college.edu",
                "password_hash": hashed_password,
                "is_active": True,
                "department_id": dept_ids[dept_code]
            })

        # Students
        student_names = [
            ("Ram", "Kumar"), ("Priya", "Sharma"), ("Aarav", "Patel"), ("Sneha", "Reddy"), ("Karthik", "Raja"),
            ("Ananya", "Sen"), ("Rahul", "Varma"), ("Diya", "Nair"), ("Kabir", "Singh"), ("Meera", "Joshi"),
            ("Vikram", "Rao"), ("Tara", "Das"), ("Aswin", "Kumar")
        ]
        for i, sid in enumerate(student_ids):
            first, last = student_names[i]
            dept_code = "CSE" if i < 6 else "AIML"
            class_id = class_cs_id if i < 6 else class_aiml_id
            student_type = "day_scholar" if i % 2 == 0 else "hosteller"
            
            student_doc = {
                "_id": sid,
                "user_id": f"PIT-STU-2023-{i:03d}",
                "role": "student",
                "name": f"{first} {last}",
                "first_name": first,
                "last_name": last,
                "email": f"student{i}@college.edu",
                "password_hash": hashed_password,
                "is_active": True,
                "department_id": dept_ids[dept_code],
                "class_id": class_id,
                "course": f"B.Tech {dept_code}",
                "current_semester": 4,
                "section": "A",
                "roll_number": f"23{dept_code}0{i+1:02d}",
                "cgpa": 6.8 if i == 0 else round(random.uniform(7.5, 9.5), 2),
                "student_type": student_type,
                "mentor_id": hod_cs_id if dept_code == "CSE" else hod_math_id,
            }
            if student_type == "hosteller":
                student_doc.update({
                    "hostel_id": "Tech Campus Residence",
                    "block": "Block C",
                    "room_number": f"{100 + i}",
                    "bed_number": "A",
                    "hostel_status": "Active"
                })
            else:
                student_doc.update({
                    "bus_number": "PIT-BUS-12",
                    "route_id": "Route 4B",
                    "pickup_point": "Guindy Metro Station"
                })
            users.append(student_doc)

        self.db.users.insert_many(users)

        # Timetable
        self.db.timetables.insert_one({"class_id": class_cs_id, "schedule": "Mon-Fri 9AM-3PM"})
        self.db.timetables.insert_one({"class_id": class_aiml_id, "schedule": "Mon-Fri 9AM-3PM"})

        # Attendance & Results & Assignments
        for i, sid in enumerate(student_ids):
            class_id = class_cs_id if i < 6 else class_aiml_id
            is_at_risk = (i == 0)
            
            # Attendance
            for day in range(20):
                date_str = (datetime.now() - timedelta(days=day)).strftime("%Y-%m-%d")
                status = "absent" if is_at_risk and day % 2 == 0 else "present"
                self.db.attendance.insert_one({
                    "student_id": sid,
                    "class_id": class_id,
                    "subject_code": "CS201" if i < 6 else "AM201",
                    "date": date_str,
                    "status": status
                })
                
            # Results
            subj = "CS201" if i < 6 else "AM201"
            if is_at_risk:
                self.db.results.insert_one({"student_id": sid, "exam_name": "Unit Test 1", "subject_code": subj, "score": 78})
                self.db.results.insert_one({"student_id": sid, "exam_name": "Internal Assessment 1", "subject_code": subj, "score": 64})
                self.db.results.insert_one({"student_id": sid, "exam_name": "Model Exam", "subject_code": subj, "score": 55})
            else:
                self.db.results.insert_one({"student_id": sid, "exam_name": "Unit Test 1", "subject_code": subj, "score": 85})
                self.db.results.insert_one({"student_id": sid, "exam_name": "Internal Assessment 1", "subject_code": subj, "score": 90})

        # Seed Assignments & Submissions
        for cls_id in [class_cs_id, class_aiml_id]:
            asg_id = self.db.assignments.insert_one({
                "title": "Homework 1 - Core Foundations",
                "class_id": cls_id,
                "due_date": "2026-08-15"
            }).inserted_id
            
            for idx, sid in enumerate(student_ids):
                student_cls_id = class_cs_id if idx < 6 else class_aiml_id
                if student_cls_id != cls_id:
                    continue
                if idx == 0:
                    self.db.submissions.insert_one({
                        "assignment_id": asg_id,
                        "student_id": sid,
                        "title": "Homework 1 - Core Foundations",
                        "status": "pending",
                        "due_date": "2026-08-15",
                        "is_late": True
                    })
                else:
                    self.db.submissions.insert_one({
                        "assignment_id": asg_id,
                        "student_id": sid,
                        "title": "Homework 1 - Core Foundations",
                        "status": "graded",
                        "due_date": "2026-08-15",
                        "score": random.randint(75, 100),
                        "is_late": False
                    })

        # Active Interventions
        self.db.interventions.insert_one({
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
                "assignment_rate": "0% Completion"
            },
            "suggested_action": "Schedule 1-on-1 concept mentoring session, provide homework catch-up worksheets.",
            "teacher_notes": "First mentoring scheduled.",
            "faculty_notes": "First mentoring scheduled.",
            "outcome_metrics": {
                "initial_attendance": 55.0,
                "current_attendance": 70.0,
                "initial_grade_avg": 65.7,
                "current_grade_avg": 72.0,
                "improvement_status": "Positive Progress"
            }
        })
        
        # Seed notices
        self.db.notices.insert_one({
            "title": "Welcome to PIT",
            "content": "Portalitics Institute of Technology academic platform is now active.",
            "visibility": ["student", "faculty", "hod"],
            "createdAt": datetime.utcnow()
        })
        print("[SUCCESS] In-memory mongomock database auto-seeded successfully!")

mongo_client = MongoDBClient()
