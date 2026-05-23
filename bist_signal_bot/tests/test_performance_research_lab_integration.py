import pytest
from bist_signal_bot.research_lab.budget import ResearchBudgetManager
from bist_signal_bot.research_lab.models import ResearchJob, ResearchJobType, ResearchJobRiskLevel

def test_budget_estimate_uses_baseline():
    mgr = ResearchBudgetManager()
    job = ResearchJob(
        job_id="j1",
        title="test",
        job_type=ResearchJobType.BACKTEST,
        priority="NORMAL",
        max_runtime_seconds=600,
        risk_level=ResearchJobRiskLevel.SAFE
    )
    est = mgr.estimate_job_cost(job)
    assert est is not None
    assert "estimated_runtime" in est
