from typing import Dict, Any, List
from app.core.config import settings

class DeterministicRulesEngine:
    """
    Deterministic Python Rules Engine (Factual & Evidence Layer).
    Ensures that numeric risk scores, threshold checks, and trend metrics are calculated
    with 100% precision in Python BEFORE any AI LLM is consulted.
    """

    @staticmethod
    def calculate_attendance_metric(attendance_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not attendance_records:
            return {"percentage": 100.0, "trend": "Stable", "total_sessions": 0, "absences": 0, "recent_percentage": 100.0}

        total = len(attendance_records)
        present = sum(1 for r in attendance_records if r.get("status") in ["present", "late"])
        pct = round((present / total) * 100, 1)

        # Calculate recent trend (last 5 vs total)
        recent = attendance_records[:5] if len(attendance_records) >= 5 else attendance_records
        recent_present = sum(1 for r in recent if r.get("status") in ["present", "late"])
        recent_pct = (recent_present / len(recent)) * 100 if recent else pct

        if recent_pct < pct - 5:
            trend = "Declining"
        elif recent_pct > pct + 5:
            trend = "Improving"
        else:
            trend = "Stable"

        return {
            "percentage": pct,
            "trend": trend,
            "total_sessions": total,
            "absences": total - present,
            "recent_percentage": round(recent_pct, 1)
        }

    @staticmethod
    def calculate_grade_metric(exam_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not exam_records:
            return {"average_score": 85.0, "trend": "Steady", "subject_breakdown": {}, "consecutive_drops": 0, "weak_subjects": []}

        subject_scores = {}
        history = []

        for exam in exam_records:
            subj = exam.get("subject", "General")
            score = float(exam.get("score", 0))
            history.append(score)
            if subj not in subject_scores:
                subject_scores[subj] = []
            subject_scores[subj].append(score)

        avg_score = round(sum(history) / len(history), 1) if history else 0.0

        # Check for consecutive drops
        consecutive_drops = 0
        for i in range(1, len(history)):
            if history[i] < history[i-1]:
                consecutive_drops += 1
            else:
                consecutive_drops = 0

        # Identify weak subjects (latest score < 60 or avg < 65)
        weak_subjects = []
        for subj, scores in subject_scores.items():
            if (sum(scores) / len(scores)) < 65 or (scores and scores[-1] < 60):
                weak_subjects.append(subj)

        trend = "Needs Support" if consecutive_drops >= 2 or len(weak_subjects) > 0 else "Steady"

        return {
            "average_score": avg_score,
            "history": history,
            "trend": trend,
            "consecutive_drops": consecutive_drops,
            "weak_subjects": weak_subjects,
            "subject_breakdown": {s: round(sum(sc)/len(sc), 1) for s, sc in subject_scores.items()}
        }

    @staticmethod
    def calculate_assignment_metric(assignment_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not assignment_records:
            return {"completion_rate": 100.0, "delays_count": 0, "missed_count": 0, "total_assigned": 0}

        total = len(assignment_records)
        submitted = sum(1 for a in assignment_records if a.get("status") in ["submitted", "graded"])
        delays = sum(1 for a in assignment_records if a.get("is_late", False))
        missed = total - submitted

        completion_rate = round((submitted / total) * 100, 1) if total > 0 else 100.0

        return {
            "completion_rate": completion_rate,
            "delays_count": delays,
            "missed_count": missed,
            "total_assigned": total
        }

    @classmethod
    def compute_multi_signal_score(cls, attendance: Dict[str, Any], grades: Dict[str, Any], assignments: Dict[str, Any]) -> Dict[str, Any]:
        w_att = settings.RISK_WEIGHT_ATTENDANCE
        w_grd = settings.RISK_WEIGHT_GRADES
        w_asg = settings.RISK_WEIGHT_ASSIGNMENTS
        w_del = settings.RISK_WEIGHT_SUBMISSION_DELAYS

        # 0 to 100 Risk Score
        att_risk = max(0, (100 - attendance.get("percentage", 100))) * 1.2
        if attendance.get("trend") == "Declining":
            att_risk += 15.0

        grd_risk = max(0, (100 - grades.get("average_score", 100))) * 1.1
        if grades.get("consecutive_drops", 0) >= 2:
            grd_risk += 20.0

        asg_risk = max(0, (100 - assignments.get("completion_rate", 100)))
        del_risk = min(100, assignments.get("delays_count", 0) * 20.0 + assignments.get("missed_count", 0) * 30.0)

        composite_risk = round(
            (att_risk * w_att) +
            (grd_risk * w_grd) +
            (asg_risk * w_asg) +
            (del_risk * w_del),
            1
        )
        composite_risk = min(100.0, max(0.0, composite_risk))

        # Map to human-friendly non-technical priority tiers
        if composite_risk >= settings.AT_RISK_IMMEDIATE_THRESHOLD:
            support_tier = "Immediate Attention Needed"
            badge_color = "dark-red"
            action_code = "CRITICAL"
        elif composite_risk >= settings.AT_RISK_SUPPORT_THRESHOLD:
            support_tier = "Support Recommended"
            badge_color = "crimson"
            action_code = "NEEDS_ATTENTION"
        else:
            support_tier = "On Track"
            badge_color = "light-red"
            action_code = "MONITOR"

        return {
            "composite_score": composite_risk,
            "support_tier": support_tier,
            "badge_color": badge_color,
            "action_code": action_code,
            "signals": {
                "attendance_percentage": attendance.get("percentage"),
                "attendance_trend": attendance.get("trend"),
                "grade_average": grades.get("average_score"),
                "consecutive_grade_drops": grades.get("consecutive_drops"),
                "weak_subjects": grades.get("weak_subjects", []),
                "assignment_completion": assignments.get("completion_rate"),
                "delays": assignments.get("delays_count")
            }
        }
