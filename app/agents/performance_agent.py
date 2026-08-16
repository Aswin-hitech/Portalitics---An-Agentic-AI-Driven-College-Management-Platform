from typing import Dict, Any
from app.services.rules_engine import DeterministicRulesEngine
from app.services.mongo_client import mongo_client

class PerformanceAnalysisAgent:
    """
    Agent 1: Performance Analysis Agent
    Decision Owned: "What changed in academic metrics?"
    Calculates attendance %, assignment completion, exam trends, and subject weakness directly from MongoDB.
    """
    def execute(self, student_id: str) -> Dict[str, Any]:
        student = mongo_client.get_user_by_id(student_id)
        student_name = student.get("name", "Student") if student else "Student"
        raw_data = mongo_client.get_student_academic_history(student_id)

        att_metric = DeterministicRulesEngine.calculate_attendance_metric(raw_data.get("attendance", []))
        grd_metric = DeterministicRulesEngine.calculate_grade_metric(raw_data.get("exams", []))
        asg_metric = DeterministicRulesEngine.calculate_assignment_metric(raw_data.get("assignments", []))

        return {
            "student_id": student_id,
            "student_name": student_name,
            "attendance": att_metric,
            "grades": grd_metric,
            "assignments": asg_metric
        }

performance_agent = PerformanceAnalysisAgent()
