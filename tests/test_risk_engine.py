import pytest
from app.services.rules_engine import DeterministicRulesEngine

def test_attendance_metric_calculation():
    records = [
        {"status": "present"},
        {"status": "present"},
        {"status": "absent"},
        {"status": "absent"}
    ]
    res = DeterministicRulesEngine.calculate_attendance_metric(records)
    assert res["percentage"] == 50.0
    assert res["total_sessions"] == 4
    assert res["absences"] == 2

def test_grade_metric_calculation():
    exams = [
        {"subject": "Mathematics", "score": 78},
        {"subject": "Mathematics", "score": 64},
        {"subject": "Mathematics", "score": 55}
    ]
    res = DeterministicRulesEngine.calculate_grade_metric(exams)
    assert res["consecutive_drops"] == 2
    assert "Mathematics" in res["weak_subjects"]

def test_multi_signal_scoring():
    att = {"percentage": 72.0, "trend": "Declining"}
    grd = {"average_score": 65.7, "consecutive_drops": 2, "weak_subjects": ["Mathematics"]}
    asg = {"completion_rate": 68.0, "delays_count": 2, "missed_count": 1}

    score = DeterministicRulesEngine.compute_multi_signal_score(att, grd, asg)
    assert score["composite_score"] > 30.0
    assert score["support_tier"] in ["Support Recommended", "Immediate Attention Needed"]
