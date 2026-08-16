import os
import json
from typing import Dict, Any
from app.core.config import settings

class GroqLLMClient:
    """
    Groq LLM Client for PORTALITICS Explainable AI.
    Generates explainable insights in normal non-technical college language:
    Observation -> Evidence -> Reason -> Recommendation
    """
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL or "llama3-8b-8192"

    def generate_evidence_grounded_recommendation(
        self,
        student_name: str,
        rules_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        signals = rules_output.get("signals", {})
        tier = rules_output.get("support_tier", "Support Recommended")
        score = rules_output.get("composite_score", 45.0)

        att_pct = signals.get("attendance_percentage", 75)
        att_trend = signals.get("attendance_trend", "Declining")
        grd_avg = signals.get("grade_average", 60)
        drops = signals.get("consecutive_grade_drops", 2)
        weaks = signals.get("weak_subjects", ["Mathematics"])
        weak_str = ", ".join(weaks) if weaks else "Algebra & Calculus"

        # Baseline rule-based fallback values
        if tier == "Immediate Attention Needed":
            observation = f"Academic engagement and assessment scores require immediate faculty review in {weak_str}."
            evidence = f"Class attendance dropped to {att_pct}% ({att_trend} trend); test scores decreased across {drops} consecutive assessments (average {grd_avg}/100)."
            reason = f"Consecutive assessment drops combined with attendance dip below 75% indicates difficulty grasping core concepts in {weak_str}."
            recommendation = f"Schedule a 1-on-1 concept revision session with the faculty mentor, assign a peer study partner, and monitor weekly attendance."
        elif tier == "Support Recommended":
            observation = f"Early signs of academic friction and homework submission delays in {weak_str}."
            evidence = f"Attendance is at {att_pct}% ({att_trend}) with test average of {grd_avg}/100 and recent late homework submissions."
            reason = f"Minor assignment delays and test score fluctuations suggest a need for structured time management and concept review."
            recommendation = f"Conduct an informal academic progress check-in, provide extra practice worksheets in {weak_str}, and set up weekly goal reminders."
        else:
            observation = f"Consistently strong academic performance and steady course participation."
            evidence = f"Attendance maintained at {att_pct}%, strong exam average of {grd_avg}/100 with zero missing assignments."
            reason = f"High attendance and consistent exam performance indicate mastery of core curriculum topics."
            recommendation = f"Encourage advanced problem-solving projects, peer mentoring opportunities, and participation in university technical hackathons."

        # Attempt to call ChatGroq via LangChain if key is present
        if self.api_key and self.api_key.strip() and self.api_key != "MOCK_KEY":
            try:
                from langchain_groq import ChatGroq
                from langchain_core.prompts import ChatPromptTemplate
                from langchain_core.output_parsers import JsonOutputParser
                
                llm = ChatGroq(
                    api_key=self.api_key,
                    model_name=self.model,
                    temperature=0.2
                )
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are an academic support agent. Generate a structured intervention plan in JSON format."),
                    ("user", """Generate a structured intervention plan for student {student_name} based on:
                    - Support Tier: {tier}
                    - Composite Risk Score: {score}/100
                    - Attendance: {att_pct}% ({att_trend} trend)
                    - Grade Average: {grd_avg}/100
                    - Grade Drops: {drops} consecutive assessments
                    - Weak Subject Areas: {weak_str}
                    
                    Provide a JSON response with exactly these keys:
                    "observation" (string): Short description of academic engagement.
                    "evidence" (string): Academic stats supporting the observation.
                    "reason" (string): The underlying educational issue (e.g. concept gaps, time management).
                    "recommendation" (string): Actionable advice for the faculty to help the student.""")
                ])
                
                chain = prompt | llm | JsonOutputParser()
                data = chain.invoke({
                    "student_name": student_name,
                    "tier": tier,
                    "score": score,
                    "att_pct": att_pct,
                    "att_trend": att_trend,
                    "grd_avg": grd_avg,
                    "drops": drops,
                    "weak_str": weak_str
                })
                
                observation = data.get("observation", observation)
                evidence = data.get("evidence", evidence)
                reason = data.get("reason", reason)
                recommendation = data.get("recommendation", recommendation)
                print(f"[INFO] Successfully generated Groq AI insights via LangChain for {student_name}.")
            except Exception as e:
                print(f"[WARNING] LangChain ChatGroq call failed: {e}. Falling back to deterministic templates.")

        return {
            "student_name": student_name,
            "priority_tier": tier,
            "support_score": score,
            "badge_color": rules_output.get("badge_color", "crimson"),
            "observation": observation,
            "evidence": evidence,
            "reason": reason,
            "recommendation": recommendation,
            "key_signals": {
                "attendance": f"{att_pct}% ({att_trend})",
                "exam_trend": f"Average {grd_avg}/100 ({drops} consecutive drops)",
                "weak_areas": weak_str
            }
        }

groq_client = GroqLLMClient()
