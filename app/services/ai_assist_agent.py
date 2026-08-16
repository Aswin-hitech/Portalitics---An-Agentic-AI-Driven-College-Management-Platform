import re
import json
from datetime import datetime
from typing import Dict, Any, List
from app.core.config import settings
from app.services.mongo_client import mongo_client
from app.services.rules_engine import DeterministicRulesEngine
from app.agents.orchestrator import orchestrator


class AIAssistAgent:
    """
    Agentic Institutional Command Center Parser and Executor.
    Parses natural language commands from authorized staff and executes operations.
    """
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL or "llama3-8b-8192"

    def parse_intent(self, query: str, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses query using Groq LLM if available, otherwise falls back to Regex parsing.
        """
        role = user.get("role", "faculty")
        
        # If API key is present and not dummy, try calling Groq LLM
        if self.api_key and self.api_key.strip() and self.api_key != "MOCK_KEY":
            try:
                import groq
                client = groq.Groq(api_key=self.api_key)
                
                prompt = f"""
                You are the Agentic AI Command Center for Portalitics College ERP.
                Analyze the user's natural language command: "{query}"
                The active user role is "{role}".
                
                Supported actions:
                1. "update_marks": Modifies a student's score. Required params: "student_name", "subject", "score" (integer).
                2. "query_attendance": Lists students with low attendance. Required params: "threshold" (number, default 75), "department" (optional string).
                3. "student_details": Retrieves a student's academic profile. Required params: "student_name".
                4. "query_performance": Filters students scoring above a threshold. Required params: "subject", "threshold" (number, default 90).
                
                Return exactly a JSON object:
                {{
                  "action": "update_marks" | "query_attendance" | "student_details" | "query_performance" | "unknown",
                  "parameters": {{ ... }},
                  "plan": ["step 1", "step 2", "step 3"],
                  "confirmation_required": true | false
                }}
                """
                
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model,
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                
                data = json.loads(chat_completion.choices[0].message.content)
                return data
            except Exception as e:
                print(f"[WARNING] Groq intent parse failed: {e}. Using Regex fallback.")
                
        # Regex Fallback Engine
        return self._parse_regex_fallback(query)

    def _parse_regex_fallback(self, query: str) -> Dict[str, Any]:
        q = query.lower()
        
        # 1. Update marks: "Find Aswin from the AIML department and update his OOPS mark to 92"
        find_update_match = re.search(
            r'find\s+([a-zA-Z\s]+?)\s+(?:from\s+([a-zA-Z\s]+?)\s+department\s+)?and\s+update\s+(?:his|her)?\s*([a-zA-Z0-9\s]+?)\s+(?:mark|score|grade)\s+(?:to|for)\s+(\d+)',
            q, re.IGNORECASE
        )
        if find_update_match:
            student_name = find_update_match.group(1).strip()
            dept = find_update_match.group(2)
            if dept:
                dept = dept.replace("the", "").strip()
            subject = find_update_match.group(3).strip().upper()
            score = int(find_update_match.group(4))
            return {
                "action": "update_marks",
                "parameters": {"student_name": student_name, "department": dept, "subject": subject, "score": score},
                "plan": [
                    f"Search student database for candidate '{student_name}'" + (f" in department '{dept}'" if dept else ""),
                    f"Verify active user has permission to modify '{subject}' course records",
                    f"Apply score update to {score} / 100",
                    f"Log institutional modification audit trail"
                ],
                "confirmation_required": True
            }

        # Or: "update Aswin's OOPS mark to 92", "set OOPS mark for Aswin to 92"
        update_match = re.search(
            r'(?:update|set|change)\s+([a-zA-Z\s]+?)(?:\'s)?\s+(?:from\s+([a-zA-Z\s]+?)\s+department\s+)?(?:oops|database|dbms|os|mathematics|ml)?\s*([a-zA-Z0-9\s]+?)\s+(?:mark|score|grade)\s+(?:to|for)\s+(\d+)', 
            q, re.IGNORECASE
        )
        if not update_match:
            # Alternate match: "update [name] [subject] to [score]"
            update_match = re.search(
                r'update\s+([a-zA-Z\s]+?)\s+([a-zA-Z0-9\s]+?)\s+(?:mark|score\s+)?to\s+(\d+)', 
                q, re.IGNORECASE
            )
            if update_match:
                student_name = update_match.group(1).strip()
                subject = update_match.group(2).strip().upper()
                score = int(update_match.group(3))
                return {
                    "action": "update_marks",
                    "parameters": {"student_name": student_name, "subject": subject, "score": score},
                    "plan": [
                        f"Search student database for candidate '{student_name}'",
                        f"Verify active user has permission to modify '{subject}' course records",
                        f"Apply score update to {score} / 100",
                        f"Log institutional modification audit trail"
                    ],
                    "confirmation_required": True
                }
        else:
            student_name = update_match.group(1).replace("his", "").replace("her", "").strip()
            dept = update_match.group(2)
            subject = update_match.group(3).strip().upper()
            score = int(update_match.group(4))
            return {
                "action": "update_marks",
                "parameters": {"student_name": student_name, "department": dept, "subject": subject, "score": score},
                "plan": [
                    f"Search student database for candidate '{student_name}'" + (f" in department '{dept}'" if dept else ""),
                    f"Verify active user has permission to modify '{subject}' course records",
                    f"Apply score update to {score} / 100",
                    f"Log institutional modification audit trail"
                ],
                "confirmation_required": True
            }

        # 2. Query attendance: "Show all AIML students with attendance below 75%"
        attendance_match = re.search(r'attendance\s+(?:below|under|<)\s*(\d+)', q, re.IGNORECASE)
        if attendance_match:
            threshold = int(attendance_match.group(1))
            # Extract department keyword if any
            dept = None
            for d in ["aiml", "aids", "cse", "ece", "eee", "mech", "it"]:
                if d in q:
                    dept = d.upper()
                    break
            return {
                "action": "query_attendance",
                "parameters": {"threshold": threshold, "department": dept},
                "plan": [
                    f"Scan student list" + (f" filtered by department '{dept}'" if dept else ""),
                    f"Fetch historical attendance logs for each candidate",
                    f"Filter results for attendance averages below {threshold}%"
                ],
                "confirmation_required": False
            }

        # 3. Student details: "Get Aswin's complete academic details"
        details_match = re.search(r'(?:details for|get|show|find student)\s+([a-zA-Z\s]+)', q, re.IGNORECASE)
        if details_match:
            student_name = details_match.group(1).replace("'s", "").replace("complete academic details", "").strip()
            return {
                "action": "student_details",
                "parameters": {"student_name": student_name},
                "plan": [
                    f"Retrieve user profile for '{student_name}'",
                    f"Compile current enrollment and course results",
                    f"Retrieve active intervention statuses"
                ],
                "confirmation_required": False
            }

        # 4. Query performance: "Find students who scored above 90 in OOPS"
        perf_match = re.search(r'scored\s+(?:above|over|>)\s*(\d+)\s+in\s+([a-zA-Z0-9\s]+)', q, re.IGNORECASE)
        if perf_match:
            threshold = int(perf_match.group(1))
            subject = perf_match.group(2).strip().upper()
            return {
                "action": "query_performance",
                "parameters": {"subject": subject, "threshold": threshold},
                "plan": [
                    f"Scan central results logs for course '{subject}'",
                    f"Filter scores above {threshold} / 100",
                    f"Resolve student candidate details"
                ],
                "confirmation_required": False
            }

        return {
            "action": "unknown",
            "parameters": {},
            "plan": ["Analyze query parameters", "Match query patterns"],
            "confirmation_required": False
        }

    def _find_student_fuzzy(self, student_name: str):
        import re
        student_name = re.sub(r'[^\w\s-]', '', student_name).strip()
        if not student_name:
            return None
            
        student = mongo_client.db.users.find_one({
            "role": "student",
            "name": {"$regex": f"^{student_name}", "$options": "i"}
        })
        if student:
            return student
            
        student = mongo_client.db.users.find_one({
            "role": "student",
            "name": {"$regex": student_name, "$options": "i"}
        })
        if student:
            return student
            
        tokens = [t for t in student_name.split() if len(t) > 2]
        for t in tokens:
            student = mongo_client.db.users.find_one({
                "role": "student",
                "name": {"$regex": t, "$options": "i"}
            })
            if student:
                return student
        return None

    def execute_command(self, parsed: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes database actions or read queries based on parsed intents.
        """
        action = parsed.get("action", "unknown")
        params = parsed.get("parameters", {})
        user_email = user.get("email", "unknown")
        user_role = user.get("role", "faculty")
        
        # Security Authorization Block
        if user_role not in ["faculty", "hod", "admin"]:
            return {
                "status": "error",
                "message": "Authorization Denied. Only staff members can access the Command Center.",
                "audit": None
            }
            
        if action == "update_marks":
            student_name = params.get("student_name", "")
            subject = params.get("subject", "").upper()
            score = params.get("score", 0)
            
            # Find student matching name (fuzzy)
            student = self._find_student_fuzzy(student_name)
            if not student:
                return {
                    "status": "error",
                    "message": f"Verify Step Failed: Student '{student_name}' was not found in the roster. Please verify name spelling.",
                    "audit": None
                }
            
            student_id = str(student["_id"])
            
            # Log audit trail
            audit_doc = {
                "user": user_email,
                "action": "update_marks",
                "target_student_id": student_id,
                "target_student_name": student["name"],
                "subject": subject,
                "new_score": score,
                "timestamp": datetime.utcnow().isoformat()
            }
            mongo_client.db.auditLogs.insert_one(audit_doc)
            audit_doc["id"] = str(audit_doc.pop("_id"))
            
            # Perform update
            exam_id = f"EXM_AI_{int(datetime.utcnow().timestamp())}"
            mongo_client.record_exam_mark(student_id, exam_id, "Manual entry via AI Assist", subject, score)
            
            # Trigger risk engine re-analysis
            orchestrator.route_event("exam_result_added", student_id, "faculty")
            
            return {
                "status": "success",
                "message": f"Execute & Report Step Completed: Successfully updated {student['name']}'s {subject} score to {score}/100.",
                "data": {"student": student["name"], "subject": subject, "score": score},
                "audit": audit_doc
            }
            
        elif action == "query_attendance":
            threshold = float(params.get("threshold", 75))
            dept = params.get("department", None)
            
            query_filter = {"role": "student"}
            if dept:
                query_filter["department_name"] = {"$regex": f"^{dept}", "$options": "i"}
                
            students = list(mongo_client.db.users.find(query_filter))
            flagged = []
            for s in students:
                s_id = str(s["_id"])
                history = mongo_client.get_student_academic_history(s_id)
                att_metric = DeterministicRulesEngine.calculate_attendance_metric(history.get("attendance", []))
                pct = att_metric.get("percentage", 100.0)
                if pct < threshold:
                    flagged.append({
                        "name": s["name"],
                        "email": s["email"],
                        "attendance": f"{pct:.1f}%",
                        "department": s.get("department_name", "N/A")
                    })
            return {
                "status": "success",
                "message": f"Verify & Retrieve Step Completed: Found {len(flagged)} students with attendance below {threshold}%.",
                "data": flagged,
                "audit": None
            }
            
        elif action == "student_details":
            student_name = params.get("student_name", "")
            student = self._find_student_fuzzy(student_name)
            if not student:
                return {
                    "status": "error",
                    "message": f"Student '{student_name}' was not found in the roster. Please verify name spelling.",
                    "audit": None
                }
            s_id = str(student["_id"])
            history = mongo_client.get_student_academic_history(s_id)
            
            details = {
                "name": student["name"],
                "email": student["email"],
                "course": student.get("course", "N/A"),
                "cgpa": student.get("cgpa", "N/A"),
                "attendance_percentage": f"{DeterministicRulesEngine.calculate_attendance_metric(history.get('attendance', [])).get('percentage', 100.0):.1f}%",
                "recent_scores": [f"{r['subject']}: {r['score']}" for r in history.get("exams", [])[:4]]
            }
            return {
                "status": "success",
                "message": f"Retrieve Step Completed: Compiled details for {student['name']}.",
                "data": details,
                "audit": None
            }
            
        elif action == "query_performance":
            subject = params.get("subject", "")
            threshold = float(params.get("threshold", 90))
            
            results = list(mongo_client.db.results.find({
                "subject": {"$regex": subject, "$options": "i"},
                "score": {"$gt": threshold}
            }))
            
            matches = []
            for r in results:
                s_id = r["student_id"]
                student = mongo_client.get_user_by_id(s_id)
                if student:
                    matches.append({
                        "name": student.get("name", "Student"),
                        "subject": r["subject"],
                        "score": r["score"],
                        "exam_name": r.get("exam_name", "Test")
                    })
            return {
                "status": "success",
                "message": f"Verify & Retrieve Step Completed: Found {len(matches)} students scoring above {threshold} in {subject}.",
                "data": matches,
                "audit": None
            }
            
        return {
            "status": "warning",
            "message": "AI Assist received command but could not extract a matching transaction. Please verify query structure.",
            "data": None,
            "audit": None
        }

ai_assist_agent = AIAssistAgent()
