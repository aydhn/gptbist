import pytest
from bist_signal_bot.scheduler.executor import ScheduledJobExecutor
from bist_signal_bot.scheduler.models import ScheduledJob, ScheduledJobType, ScheduledJobStatus, ScheduleTrigger, ScheduleTriggerType

class MockSettings:
    DATA_DIR = "data"
    SCHEDULER_JOB_LOCK_TTL_SECONDS = 1800
    SCHEDULER_REQUIRE_GOVERNANCE_GATE = False

def test_executor_dry_run():
    exec = ScheduledJobExecutor(settings=MockSettings())
    job = ScheduledJob(
        job_id="j1", name="test", job_type=ScheduledJobType.HEALTHCHECK, status=ScheduledJobStatus.ENABLED,
        trigger=ScheduleTrigger(trigger_id="t1", trigger_type=ScheduleTriggerType.MANUAL, timezone="UTC")
    )

    run = exec.execute(job, dry_run=True)

    assert run.status == ScheduledJobStatus.SUCCESS
    assert "Executed in dry-run mode" in run.warnings
