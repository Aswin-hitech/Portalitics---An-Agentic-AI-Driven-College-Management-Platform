from typing import Dict, Any, List
from app.services.mongo_client import mongo_client

class InterventionService:
    """
    Manages Student Support Queue & 14-Day Growth Outcome Tracking for PORTALITICS.
    Queries and persists learning support records directly in MongoDB.
    """
    def get_teacher_queue(self, teacher_id: str) -> List[Dict[str, Any]]:
        return mongo_client.get_faculty_support_queue(teacher_id)

    def get_all_interventions(self) -> List[Dict[str, Any]]:
        return mongo_client.get_all_interventions()

    def get_intervention_by_id(self, intervention_id: str) -> Dict[str, Any]:
        return mongo_client.get_intervention_by_id(intervention_id) or {}

    def initiate_intervention(self, student_id: str, student_name: str, teacher_id: str, teacher_name: str, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        total = len(mongo_client.get_all_interventions()) + 1
        doc = {
            "intervention_id": f"ITV_{total:03d}",
            "student_id": student_id,
            "student_name": student_name,
            "faculty_id": teacher_id,
            "faculty_name": teacher_name,
            "course_name": recommendation.get("course_name", "Mathematics & Computer Science"),
            "priority_tier": recommendation.get("priority_tier", "Support Recommended"),
            "action_code": recommendation.get("action_code", "NEEDS_ATTENTION"),
            "status": "In Progress",
            "created_at": recommendation.get("created_at", "2026-08-10"),
            "evaluation_due": recommendation.get("evaluation_due", "2026-08-24"),
            "key_signals": recommendation.get("key_signals", {}),
            "suggested_action": recommendation.get("suggested_action", "Provide personalized academic mentoring"),
            "faculty_notes": "Support plan initiated.",
            "outcome_metrics": recommendation.get("outcome_metrics", {
                "initial_attendance": 72.0,
                "current_attendance": 84.0,
                "initial_grade_avg": 55.0,
                "current_grade_avg": 68.0,
                "improvement_status": "Positive Progress (+12% Attendance, +13 Marks)"
            })
        }
        return mongo_client.initiate_intervention(doc)

    def update_intervention_status(self, intervention_id: str, new_status: str, notes: str) -> Dict[str, Any]:
        return mongo_client.update_intervention_status(intervention_id, new_status, notes)

    def calculate_institution_outcomes(self) -> Dict[str, Any]:
        return mongo_client.calculate_institution_outcomes()

intervention_service = InterventionService()
