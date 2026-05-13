import pytest
from bist_signal_bot.runtime.jobs import RuntimeJobRunner
from bist_signal_bot.runtime.models import RuntimeJobType, RuntimeJobStatus, SessionPolicy

def test_job_runner_success():
    from bist_signal_bot.config.settings import Settings
    s = Settings()
    s.RUNTIME_JOB_TIMEOUT_SECONDS = 30
    runner = RuntimeJobRunner(settings=s)
    res = runner.run_job(RuntimeJobType.HEALTHCHECK, lambda: {"status": "ok"})

    assert res.status == RuntimeJobStatus.SUCCESS
    assert res.summary["status"] == "ok"
    assert res.attempts == 1

def test_job_runner_failure():
    from bist_signal_bot.config.settings import Settings
    s = Settings()
    s.RUNTIME_JOB_TIMEOUT_SECONDS = 30
    runner = RuntimeJobRunner(settings=s)

    def failing_func():
        raise ValueError("Simulated error")

    res = runner.run_job(RuntimeJobType.HEALTHCHECK, failing_func)

    assert res.status == RuntimeJobStatus.FAILED
    assert "Simulated error" in str(res.issues)

def test_job_runner_session_policy():
    from bist_signal_bot.config.settings import Settings
    s = Settings()
    s.RUNTIME_JOB_TIMEOUT_SECONDS = 30
    runner = RuntimeJobRunner(settings=s)
    can_run, msg = runner.should_run_in_session(SessionPolicy.RUN_ALWAYS)
    assert can_run
