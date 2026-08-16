from typing import Dict, Any
from app.agents.performance_agent import performance_agent
from app.agents.risk_agent import risk_agent
from app.agents.report_agent import report_agent
from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda
from app.services.mongo_client import mongo_client
from app.core.logging import logger
from datetime import datetime

# Define Specialist Agents as LangChain Tools
@tool
def calculate_student_performance(student_id: str) -> Dict[str, Any]:
    """Calculates student academic performance metrics including grade averages, attendance percentages, and assignment submissions."""
    logger.info(f"[LangChain Tool] Running performance analysis for student: {student_id}")
    return performance_agent.execute(student_id)

@tool
def evaluate_student_risk(perf_data: Dict[str, Any]) -> Dict[str, Any]:
    """Runs deterministic rule checks and LLM inference to calculate student composite risk and support recommendations."""
    logger.info(f"[LangChain Tool] Evaluating support risks for student: {perf_data.get('student_name')}")
    return risk_agent.execute(perf_data)

@tool
def generate_role_report(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Formats student-specific academic summary metrics and tips tailored for students, teachers, or administrators.
    Expected keys: 'role' (str), 'perf_data' (dict), 'risk_data' (dict).
    """
    role = inputs.get("role", "student")
    perf_data = inputs.get("perf_data", {})
    risk_data = inputs.get("risk_data", {})
    logger.info(f"[LangChain Tool] Generating academic report card for role: {role}")
    return report_agent.execute(role, perf_data, risk_data)

class AgentOrchestrator:
    """
    Central LangChain Router / Orchestrator Agent.
    Routes incoming user events to specialist agents via LangChain Tool Bindings and LCEL.
    """
    def __init__(self):
        # Define sequential runnables
        self._perf_step = RunnableLambda(lambda inputs: {
            **inputs,
            "perf_data": calculate_student_performance.invoke({"student_id": inputs["student_id"]})
        })
        
        self._risk_step = RunnableLambda(lambda inputs: {
            **inputs,
            "risk_data": evaluate_student_risk.invoke({"perf_data": inputs["perf_data"]})
        })
        
        self._report_step = RunnableLambda(lambda inputs: {
            **inputs,
            "report_data": generate_role_report.invoke({
                "inputs": {
                    "role": inputs["target_role"],
                    "perf_data": inputs["perf_data"],
                    "risk_data": inputs["risk_data"]
                }
            })
        })
        
        # Combine using LCEL pipe operator
        self._chain = self._perf_step | self._risk_step | self._report_step

    def route_event(self, event_type: str, student_id: str, target_role: str = "student") -> Dict[str, Any]:
        logger.info(f"[Orchestrator] Routing event '{event_type}' for student: {student_id}")
        
        # Execute LangChain Runnable Sequence
        result = self._chain.invoke({
            "event_type": event_type,
            "student_id": student_id,
            "target_role": target_role
        })
        
        # Write agent execution audit trail to MongoDB agent_logs collection
        try:
            mongo_client.db.agent_logs.insert_one({
                "event_type": event_type,
                "student_id": student_id,
                "target_role": target_role,
                "timestamp": datetime.utcnow().isoformat(),
                "composite_risk_score": result["risk_data"].get("composite_score", 0.0),
                "support_tier": result["risk_data"].get("support_tier", "On Track")
            })
        except Exception as e:
            logger.error(f"[Orchestrator] Failed to log agent audit trail: {e}")
        
        return {
            "event_type": event_type,
            "performance_metrics": result["perf_data"],
            "support_evaluation": result["risk_data"],
            "formatted_report": result["report_data"]
        }

orchestrator = AgentOrchestrator()
