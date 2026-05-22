import pytest
from bist_signal_bot.app.scheduler_app import create_scheduler_orchestrator

class MockSettings:
    DATA_DIR = "data"
    SCHEDULER_GLOBAL_LOCK_TTL_SECONDS = 3600
    SCHEDULER_JOB_LOCK_TTL_SECONDS = 1800
    SCHEDULER_DEDUPE_WINDOW_MINUTES = 30
    SCHEDULER_RUN_DUE_LIMIT = 10
    SCHEDULER_REQUIRE_GOVERNANCE_GATE = False

def test_orchestrator_default_jobs(tmp_path):
    settings = MockSettings()
    settings.DATA_DIR = str(tmp_path)
    orch = create_scheduler_orchestrator(settings, tmp_path)

    defaults = orch.default_jobs()
    assert len(defaults) > 0
    assert defaults[0].job_id == "job_default_healthcheck"
