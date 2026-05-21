import pytest
from bist_signal_bot.research_lab.planner import ResearchJobPlanner
from bist_signal_bot.research_lab.models import ResearchJobType

def test_planner_daily_plan():
    planner = ResearchJobPlanner()
    plan = planner.plan_daily_research(["ASELS"], ["S1"])
    assert len(plan.jobs) >= 4
    types = [j.job_type for j in plan.jobs]
    assert ResearchJobType.DATA_FRESHNESS_CHECK in types
    assert ResearchJobType.DRIFT_CHECK in types

def test_planner_adaptive_mapping():
    planner = ResearchJobPlanner()
    mock_refresh = {"actions": [{"type": "RUN_BACKTEST", "symbols": ["THYAO"]}]}
    plan = planner.plan_from_adaptive_refresh(mock_refresh)
    assert len(plan.jobs) == 1
    assert plan.jobs[0].job_type == ResearchJobType.BACKTEST

def test_planner_drift_mapping():
    planner = ResearchJobPlanner()
    mock_drift = {"recommended_actions": [{"type": "RETRAIN_MODEL"}]}
    plan = planner.plan_from_drift_result(mock_drift)
    assert len(plan.jobs) == 1
    assert plan.jobs[0].job_type == ResearchJobType.ML_RETRAIN
