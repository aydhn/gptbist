import pytest
from bist_signal_bot.research_lab.executor import ResearchJobExecutor
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.research_lab.models import ResearchJob, ResearchJobType, ResearchLabPolicy, ResearchJobStatus, ResearchJobRiskLevel

@pytest.fixture
def executor(tmp_path):
    return ResearchJobExecutor(settings=Settings(), base_dir=tmp_path)

def test_executor_internal_dispatch(executor):
    job = ResearchJob(job_id="x", job_type=ResearchJobType.DATA_FRESHNESS_CHECK, title="A")
    pol = ResearchLabPolicy()
    res = executor.execute_job(job, pol)
    assert res.status == ResearchJobStatus.SUCCESS
    assert "dispatched_internal" in res.metadata

def test_executor_heavy_confirm_block(executor):
    job = ResearchJob(job_id="y", job_type=ResearchJobType.CUSTOM, title="B", risk_level=ResearchJobRiskLevel.REQUIRES_CONFIRM)
    pol = ResearchLabPolicy()
    res = executor.execute_job(job, pol)
    assert res.status == ResearchJobStatus.BLOCKED
    assert any("confirmation" in e.lower() for e in res.errors)
