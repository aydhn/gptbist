import pytest
from bist_signal_bot.research_lab.models import ResearchJob, ResearchJobType, ResearchBatchPlan, ResearchBatchRun, ResearchJobTrigger, ResearchJobPriority

def test_research_job_validation():
    job = ResearchJob(
        job_id="job_1",
        job_type=ResearchJobType.BACKTEST,
        title="Test Job",
        symbols=[" asels ", "thyao"]
    )
    assert job.title == "Test Job"
    assert job.symbols == ["ASELS", "THYAO"]
    assert job.priority == ResearchJobPriority.NORMAL

def test_batch_plan_summary():
    plan = ResearchBatchPlan(
        plan_id="plan_1",
        trigger=ResearchJobTrigger.MANUAL
    )
    assert plan.plan_id == "plan_1"
    assert "research-only" in plan.disclaimer.lower()

def test_batch_run_summary():
    run = ResearchBatchRun(
        batch_id="run_1",
        status="RUNNING"
    )
    summary = run.summary()
    assert summary["batch_id"] == "run_1"
    assert summary["success_count"] == 0
