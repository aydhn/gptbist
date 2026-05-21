import pytest
from bist_signal_bot.research_lab.planner import ResearchJobPlanner
from bist_signal_bot.research_lab.models import ResearchJobType

def test_drift_integration_mapping():
    planner = ResearchJobPlanner()
    mock_drift = {"recommended_actions": [{"type": "RETRAIN_MODEL", "symbols": ["GARAN"]}]}
    plan = planner.plan_from_drift_result(mock_drift)
    assert len(plan.jobs) == 1
    assert plan.jobs[0].job_type == ResearchJobType.ML_RETRAIN
