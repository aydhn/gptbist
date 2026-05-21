import pytest
from bist_signal_bot.research_lab.planner import ResearchJobPlanner
from bist_signal_bot.research_lab.models import ResearchJobType

def test_adaptive_integration_mapping():
    planner = ResearchJobPlanner()
    mock_refresh = {"actions": [{"type": "RUN_BACKTEST", "symbols": ["THYAO"]}]}
    plan = planner.plan_from_adaptive_refresh(mock_refresh)
    assert len(plan.jobs) == 1
    assert plan.jobs[0].job_type == ResearchJobType.BACKTEST
