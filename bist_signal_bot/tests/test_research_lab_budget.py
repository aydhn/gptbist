import pytest
from bist_signal_bot.research_lab.budget import ResearchBudgetManager
from bist_signal_bot.research_lab.models import ResearchJob, ResearchJobType, ResearchLabPolicy, ResearchJobRiskLevel

def test_budget_heavy_job_warning():
    mgr = ResearchBudgetManager()
    j1 = ResearchJob(job_id="1", job_type=ResearchJobType.BACKTEST, title="A", risk_level=ResearchJobRiskLevel.RESOURCE_HEAVY)
    pol = ResearchLabPolicy(require_confirm_for_heavy_jobs=True)
    warnings = mgr.check_budget([j1], pol)
    assert any("heavy" in w.lower() for w in warnings)

def test_budget_time_exceeded():
    mgr = ResearchBudgetManager()
    j1 = ResearchJob(job_id="1", job_type=ResearchJobType.CUSTOM, title="A", max_runtime_seconds=5000)
    pol = ResearchLabPolicy(max_runtime_seconds_per_batch=3600)
    warnings = mgr.check_budget([j1], pol)
    assert any("exceeds max" in w.lower() for w in warnings)
