from typing import Dict, Any
from app.services.intervention_service import intervention_service

class ReportInsightAgent:
    """
    Agent 3: Report & Insight Agent
    Decision Owned: "How should this performance & support analysis be formatted for the specific user role?"
    Formats clear, actionable insights for Students, Teachers, or Institutional Admins.
    """
    def execute(self, role: str, perf_data: Dict[str, Any], risk_data: Dict[str, Any]) -> Dict[str, Any]:
        rec = risk_data.get("recommendation", {})
        rules = risk_data.get("rules_evaluation", {})

        student_name = perf_data.get("student_name", "Student")

        if role == "student":
            return {
                "title": f"Academic Growth & Support Overview for {student_name}",
                "summary": rec.get("observation", "Keep up your academic momentum!"),
                "tips": [
                    f"Focus on strengthening core concepts in {rec.get('key_signals', {}).get('weak_areas', 'Mathematics')}.",
                    "Maintain attendance consistency above 85% to stay ahead of upcoming module assessments.",
                    "Submit homework assignments prior to due date for detailed faculty review."
                ],
                "support_status": rules.get("support_tier", "On Track"),
                "badge_color": rules.get("badge_color", "light-red")
            }
        elif role == "teacher" or role == "faculty":
            return {
                "title": "Classroom Support Queue Priority",
                "student_name": student_name,
                "priority_tier": rules.get("support_tier"),
                "badge_color": rules.get("badge_color"),
                "observation": rec.get("observation"),
                "evidence_signals": rec.get("evidence"),
                "suggested_action": rec.get("recommendation"),
                "key_signals": rec.get("key_signals")
            }
        else: # admin
            from app.services.mongo_client import mongo_client
            total_students = mongo_client.db.users.count_documents({"role": "student"})
            active_interventions = mongo_client.db.interventions.count_documents({"status": "In Progress"})
            attention_needed_pct = f"{(active_interventions / (total_students or 1)) * 100:.1f}%"
            
            outcomes = intervention_service.calculate_institution_outcomes()
            return {
                "title": "Institutional Academic Growth & Support Dashboard",
                "total_monitored_students": total_students,
                "attention_needed_pct": attention_needed_pct,
                "intervention_success_rate": f"{outcomes['overall_success_rate']}%",
                "executive_summary": "Academic health across all departments remains strong. Proactive support plans show high resolution rates within 14-day tracking windows."
            }

report_agent = ReportInsightAgent()
