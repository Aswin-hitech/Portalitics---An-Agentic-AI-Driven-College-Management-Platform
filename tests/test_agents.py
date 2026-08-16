import pytest
from app.agents.orchestrator import orchestrator
from app.services.mongo_client import mongo_client

def test_agent_orchestrator_pipeline():
    student = mongo_client.register_user("Aarav Patel", "aarav.patel@edusphere.edu", "student", "Computer Science")
    result = orchestrator.route_event("attendance_updated", student["id"], "teacher")
    assert "performance_metrics" in result
    assert "support_evaluation" in result
    assert "formatted_report" in result
    assert result["formatted_report"]["title"] == "Classroom Support Queue Priority"
    assert result["performance_metrics"]["student_name"] == "Aarav Patel"
