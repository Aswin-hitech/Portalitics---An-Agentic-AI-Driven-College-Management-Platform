import json
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agents.orchestrator import orchestrator
from app.core.config import settings
from app.core.logging import logger
from app.services.mongo_client import mongo_client
from app.services.rules_engine import DeterministicRulesEngine


class AIAssistAgent:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL or "llama3-8b-8192"
        self.pending_confirmations: Dict[str, Dict[str, Any]] = {}

    def _normalize_name(self, value: str) -> str:
        return re.sub(r"[^\w\s-]", "", value or "").strip()

    def _resolve_department(self, department: Optional[str]) -> Optional[Dict[str, Any]]:
        if not department:
            return None
        matches = mongo_client.find_departments(department)
        return matches[0] if matches else None

    def _parse_llm_json(self, content: str) -> Dict[str, Any]:
        payload = json.loads(content)
        action = payload.get("action", "unknown")
        params = payload.get("parameters") or {}
        confirmation_required = bool(payload.get("confirmation_required", False))
        plan = payload.get("plan") or []
        return {
            "action": action,
            "parameters": params,
            "plan": plan,
            "confirmation_required": confirmation_required,
        }

    def parse_intent(self, query: str, user: Dict[str, Any]) -> Dict[str, Any]:
        role = user.get("role", "faculty")
        if self.api_key and self.api_key.strip() and self.api_key != "MOCK_KEY":
            try:
                import groq

                client = groq.Groq(api_key=self.api_key)
                prompt = f"""
You are the Portalitics AI Command Center.
Analyze the command: "{query}"
Active role: "{role}"

Return exactly JSON with:
- action: update_marks | query_attendance | student_details | query_performance | unknown
- parameters: object
- plan: array of strings
- confirmation_required: boolean
For destructive actions (update_marks), confirmation_required must be true.
"""
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model,
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
                data = self._parse_llm_json(chat_completion.choices[0].message.content)
                if data["action"] == "update_marks":
                    data["confirmation_required"] = True
                return data
            except Exception as exc:
                logger.warning(f"[AI ASSIST] Groq parse failed, using regex fallback: {exc}")
        return self._parse_regex_fallback(query)

    def _parse_regex_fallback(self, query: str) -> Dict[str, Any]:
        q = query.lower()
        departments = [d.get("code", "").lower() for d in mongo_client.get_all_departments()]
        if not departments:
            departments = ["aiml", "aids", "cse", "ece", "eee", "mech", "it"]

        update_patterns = [
            r"find\s+([a-zA-Z\s]+?)\s+(?:from\s+([a-zA-Z\s]+?)\s+department\s+)?and\s+update\s+(?:his|her)?\s*([a-zA-Z0-9\s]+?)\s+(?:mark|score|grade)\s+(?:to|for)\s+(\d+(?:\.\d+)?)",
            r"(?:update|set|change)\s+([a-zA-Z\s]+?)(?:'s)?\s+(?:from\s+([a-zA-Z\s]+?)\s+department\s+)?([a-zA-Z0-9\s]+?)\s+(?:mark|score|grade)\s+(?:to|for)\s+(\d+(?:\.\d+)?)",
            r"update\s+([a-zA-Z\s]+?)\s+([a-zA-Z0-9\s]+?)\s+(?:mark|score)?\s*to\s+(\d+(?:\.\d+)?)",
        ]
        for idx, pattern in enumerate(update_patterns):
            match = re.search(pattern, q, re.IGNORECASE)
            if not match:
                continue
            if idx == 2:
                student_name = match.group(1).strip()
                subject = match.group(2).strip().upper()
                score = float(match.group(3))
                return {
                    "action": "update_marks",
                    "parameters": {"student_name": student_name, "subject": subject, "score": score},
                    "plan": [f"Find student candidate '{student_name}'", f"Validate '{subject}' score change", f"Update score to {score}"],
                    "confirmation_required": True,
                }
            student_name = match.group(1).strip()
            department = match.group(2)
            subject = match.group(3).strip().upper()
            score = float(match.group(4))
            if department:
                department = department.replace("the", "").strip()
            return {
                "action": "update_marks",
                "parameters": {"student_name": student_name, "department": department, "subject": subject, "score": score},
                "plan": [f"Find student candidate '{student_name}'", f"Check department scope", f"Update score to {score}"],
                "confirmation_required": True,
            }

        attendance_match = re.search(r"attendance\s+(?:below|under|<)\s*(\d+)", q, re.IGNORECASE)
        if attendance_match:
            threshold = int(attendance_match.group(1))
            dept = next((d.upper() for d in departments if d in q), None)
            return {
                "action": "query_attendance",
                "parameters": {"threshold": threshold, "department": dept},
                "plan": ["Scan student list", "Fetch attendance history", f"Filter results below {threshold}%"],
                "confirmation_required": False,
            }

        details_match = re.search(r"(?:details for|get|show|find student)\s+([a-zA-Z\s]+)", q, re.IGNORECASE)
        if details_match:
            student_name = details_match.group(1).replace("'s", "").strip()
            return {
                "action": "student_details",
                "parameters": {"student_name": student_name},
                "plan": ["Retrieve profile", "Compile results", "Retrieve interventions"],
                "confirmation_required": False,
            }

        perf_match = re.search(r"scored\s+(?:above|over|>)\s*(\d+)\s+in\s+([a-zA-Z0-9\s]+)", q, re.IGNORECASE)
        if perf_match:
            threshold = int(perf_match.group(1))
            subject = perf_match.group(2).strip().upper()
            return {
                "action": "query_performance",
                "parameters": {"subject": subject, "threshold": threshold},
                "plan": ["Scan results", f"Filter scores above {threshold}", "Resolve student details"],
                "confirmation_required": False,
            }

        return {"action": "unknown", "parameters": {}, "plan": ["Analyze query"], "confirmation_required": False}

    def _authorized_scope(self, user: Dict[str, Any]) -> Dict[str, Any]:
        role = user.get("role", "faculty")
        if role in {"admin", "principal"}:
            return {"mode": "institution"}
        if role == "hod":
            return {"mode": "department", "department_id": user.get("department_id")}
        return {"mode": "department", "department_id": user.get("department_id")}

    def _student_candidates(self, student_name: str, department: Optional[str] = None) -> List[Dict[str, Any]]:
        normalized = self._normalize_name(student_name)
        if not normalized:
            return []

        query: Dict[str, Any] = {"role": "student", "name": {"$regex": normalized, "$options": "i"}}
        dept_doc = self._resolve_department(department)
        if dept_doc:
            query["department_id"] = dept_doc["_id"]

        students = list(mongo_client.db.users.find(query))
        if students:
            return students

        tokens = [t for t in normalized.split() if len(t) > 2]
        if not tokens:
            return []

        q = {"role": "student", "$or": [{"name": {"$regex": t, "$options": "i"}} for t in tokens]}
        if dept_doc:
            q["department_id"] = dept_doc["_id"]
        return list(mongo_client.db.users.find(q))

    def _build_preview(self, parsed: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        params = parsed.get("parameters", {})
        action = parsed.get("action", "unknown")
        if action != "update_marks":
            return {"status": "warning", "message": "Only destructive actions require confirmation preview.", "audit": None}
        candidates = self._student_candidates(params.get("student_name", ""), params.get("department"))
        return {
            "status": "confirmation_required",
            "message": "This action will modify student records. Review the preview and confirm to continue.",
            "data": {
                "student_matches": [
                    {
                        "id": str(c["_id"]),
                        "name": c.get("name"),
                        "department": c.get("department_name") or c.get("department_id"),
                        "course": c.get("course"),
                    }
                    for c in candidates[:5]
                ],
                "subject": params.get("subject"),
                "score": params.get("score"),
            },
            "audit": None,
        }

    def execute_command(self, parsed: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        action = parsed.get("action", "unknown")
        params = parsed.get("parameters", {})
        user_email = user.get("email", "unknown")
        user_role = user.get("role", "faculty")
        scope = self._authorized_scope(user)

        if user_role not in {"faculty", "hod", "admin", "principal"}:
            return {"status": "error", "message": "Authorization denied.", "audit": None}

        if action == "update_marks":
            student_name = params.get("student_name", "")
            subject = str(params.get("subject", "")).upper().strip()
            score = params.get("score", None)
            if score is None:
                return {"status": "error", "message": "Missing score.", "audit": None}
            try:
                score = float(score)
            except Exception:
                return {"status": "error", "message": "Score must be numeric.", "audit": None}
            if score < 0 or score > 100:
                return {"status": "error", "message": "Score must be between 0 and 100.", "audit": None}

            candidates = self._student_candidates(student_name, params.get("department"))
            if not candidates:
                return {"status": "error", "message": f"Student '{student_name}' was not found.", "audit": None}
            if len(candidates) > 1:
                return {
                    "status": "warning",
                    "message": f"I found {len(candidates)} matching students. Please select one.",
                    "data": {
                        "matches": [
                            {"id": str(s["_id"]), "name": s.get("name"), "department": s.get("department_name") or s.get("department_id")}
                            for s in candidates[:10]
                        ]
                    },
                    "audit": None,
                }

            student = candidates[0]
            if scope["mode"] == "department" and student.get("department_id") != scope.get("department_id"):
                return {"status": "error", "message": "You are not authorized to modify students outside your scope.", "audit": None}

            exam_name = "Manual entry via AI Assist"
            exam_id = f"EXM_AI_{int(datetime.utcnow().timestamp())}"
            before = mongo_client.db.results.find_one(
                {"student_id": student["_id"], "subject_code": subject, "exam_name": exam_name}
            )

            try:
                mongo_client.record_exam_mark(str(student["_id"]), exam_id, exam_name, subject, score)
                after = mongo_client.db.results.find_one(
                    {"student_id": student["_id"], "subject_code": subject, "exam_name": exam_name}
                )
                if not after or float(after.get("score", -1)) != float(score):
                    raise RuntimeError("Database verification failed after update.")

                orchestrator.route_event("exam_result_added", str(student["_id"]), "faculty")
                audit_doc = {
                    "user": user_email,
                    "action": "update_marks",
                    "target_student_id": str(student["_id"]),
                    "target_student_name": student["name"],
                    "subject": subject,
                    "old_score": before.get("score") if before else None,
                    "new_score": score,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "success",
                }
                mongo_client.db.auditLogs.insert_one(audit_doc)
                audit_doc["id"] = str(audit_doc.pop("_id"))
                return {
                    "status": "success",
                    "message": f"Updated {student['name']}'s {subject} score to {score}/100.",
                    "data": {"student": student["name"], "subject": subject, "score": score},
                    "audit": audit_doc,
                }
            except Exception as exc:
                audit_doc = {
                    "user": user_email,
                    "action": "update_marks",
                    "target_student_id": str(student["_id"]),
                    "target_student_name": student["name"],
                    "subject": subject,
                    "new_score": score,
                    "timestamp": datetime.utcnow().isoformat(),
                    "status": "failure",
                    "error": str(exc),
                }
                mongo_client.db.auditLogs.insert_one(audit_doc)
                audit_doc["id"] = str(audit_doc.pop("_id"))
                return {"status": "error", "message": str(exc), "audit": audit_doc}

        if action == "query_attendance":
            threshold = float(params.get("threshold", 75))
            dept = params.get("department")
            query_filter = {"role": "student"}
            if dept:
                dept_doc = self._resolve_department(dept)
                if dept_doc:
                    query_filter["department_id"] = dept_doc["_id"]
            students = list(mongo_client.db.users.find(query_filter))
            flagged = []
            for s in students:
                history = mongo_client.get_student_academic_history(str(s["_id"]))
                pct = DeterministicRulesEngine.calculate_attendance_metric(history.get("attendance", [])).get("percentage", 100.0)
                if pct < threshold:
                    flagged.append({"name": s.get("name"), "email": s.get("email"), "attendance": f"{pct:.1f}%"} )
            return {"status": "success", "message": f"Found {len(flagged)} students below {threshold}%.", "data": flagged, "audit": None}

        if action == "student_details":
            student = self._student_candidates(params.get("student_name", ""))
            if not student:
                return {"status": "error", "message": "Student not found.", "audit": None}
            if len(student) > 1:
                return {
                    "status": "warning",
                    "message": f"I found {len(student)} matching students. Please select one.",
                    "data": {"matches": [{"id": str(s["_id"]), "name": s.get("name"), "department": s.get("department_name") or s.get("department_id")} for s in student[:10]]},
                    "audit": None,
                }
            student = student[0]
            history = mongo_client.get_student_academic_history(str(student["_id"]))
            return {
                "status": "success",
                "message": f"Compiled details for {student['name']}.",
                "data": {
                    "name": student["name"],
                    "email": student["email"],
                    "course": student.get("course", "N/A"),
                    "cgpa": student.get("cgpa", "N/A"),
                    "attendance_percentage": f"{DeterministicRulesEngine.calculate_attendance_metric(history.get('attendance', [])).get('percentage', 100.0):.1f}%",
                },
                "audit": None,
            }

        if action == "query_performance":
            subject = params.get("subject", "")
            threshold = float(params.get("threshold", 90))
            dept = params.get("department")
            query = {"subject_code": {"$regex": subject, "$options": "i"}, "score": {"$gt": threshold}}
            if dept:
                dept_doc = self._resolve_department(dept)
                if dept_doc:
                    students = list(mongo_client.db.users.find({"role": "student", "department_id": dept_doc["_id"]}))
                    allowed_ids = [s["_id"] for s in students]
                    query["student_id"] = {"$in": allowed_ids}
            results = list(mongo_client.db.results.find(query))
            matches = []
            for r in results:
                student = mongo_client.get_user_by_id(r["student_id"])
                if student:
                    matches.append({"name": student.get("name", "Student"), "subject": r.get("subject_code"), "score": r.get("score"), "exam_name": r.get("exam_name", "Test")})
            return {"status": "success", "message": f"Found {len(matches)} students above {threshold} in {subject}.", "data": matches, "audit": None}

        return {"status": "warning", "message": "AI Assist could not extract a matching transaction.", "data": None, "audit": None}

    def request_confirmation(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        token = uuid.uuid4().hex
        self.pending_confirmations[token] = {"parsed": parsed, "created_at": datetime.utcnow().isoformat()}
        preview = self._build_preview(parsed, {})
        preview["confirmation_token"] = token
        preview["message"] = "This action changes records. Review the preview, then confirm to execute."
        return preview

    def confirm_and_execute(self, token: str, user: Dict[str, Any]) -> Dict[str, Any]:
        pending = self.pending_confirmations.pop(token, None)
        if not pending:
            return {"status": "error", "message": "Confirmation token expired or invalid.", "audit": None}
        return self.execute_command(pending["parsed"], user)


ai_assist_agent = AIAssistAgent()
