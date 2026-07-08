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

def test_executor_command_validation(executor):
    # Test valid command
    code, stdout, stderr = executor.execute_command(["python", "-m", "bist_signal_bot", "healthcheck"], 5, {})
    # Since we don't mock subprocess, it might return 0, 1 or timeout, but it shouldn't return the security error
    assert "Security Error" not in stderr

    # Test invalid commands
    code, stdout, stderr = executor.execute_command(["echo", "hello"], 5, {})
    assert code == 1
    assert "Security Error" in stderr

    code, stdout, stderr = executor.execute_command(["python", "script.py"], 5, {})
    assert code == 1
    assert "Security Error" in stderr

    code, stdout, stderr = executor.execute_command([], 5, {})
    assert code == 1
    assert "Security Error" in stderr

def test_executor_command_injection_blocked(executor):
    code, stdout, stderr = executor.execute_command(["python", "-m", "bist_signal_bot", ";", "echo", "EXPLOITED"], 5, {})
    assert code == 1
    assert "Security Error" in stderr

    code, stdout, stderr = executor.execute_command(["python", "-m", "bist_signal_bot", "healthcheck", "&&", "ls"], 5, {})
    assert code == 1
    assert "Security Error" in stderr

    code, stdout, stderr = executor.execute_command(["python", "-m", "bist_signal_bot", "-c", "import os"], 5, {})
    assert code == 1
    assert "Security Error" in stderr
