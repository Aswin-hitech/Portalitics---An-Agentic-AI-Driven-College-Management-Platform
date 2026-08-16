from typing import Dict, Any
from app.services.rules_engine import DeterministicRulesEngine
from app.services.groq_client import groq_client

class SupportRiskRecommendationAgent:
    """
    Agent 2: Risk & Recommendation Agent
    Decision Owned: "What does this metric mean, and what support should be provided?"
    Combines multi-signal rules engine output with Groq LLM reasoning.
    """
    def execute(self, performance_output: Dict[str, Any]) -> Dict[str, Any]:
        att = performance_output.get("attendance", {})
        grd = performance_output.get("grades", {})
        asg = performance_output.get("assignments", {})
        student_name = performance_output.get("student_name", "Student")

        # Step 1: Deterministic Multi-Signal Score
        rules_eval = DeterministicRulesEngine.compute_multi_signal_score(att, grd, asg)

        # Step 2: Evidence-Grounded AI Phrasing via Groq LLM Client
        ai_recommendation = groq_client.generate_evidence_grounded_recommendation(
            student_name=student_name,
            rules_output=rules_eval
        )

        return {
            "rules_evaluation": rules_eval,
            "recommendation": ai_recommendation
        }

risk_agent = SupportRiskRecommendationAgent()
