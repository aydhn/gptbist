import pytest
from datetime import datetime, timedelta
from bist_signal_bot.scheduler.deduplication import ScheduledJobDeduplicator
from bist_signal_bot.scheduler.models import ScheduledJob, ScheduledJobType, ScheduledJobStatus, ScheduleTrigger, ScheduleTriggerType, ScheduledJobRun, ScheduledJobDecision

def test_deduplicator():
    deduper = ScheduledJobDeduplicator()

    job = ScheduledJob(
        job_id="j1", name="test", job_type=ScheduledJobType.CUSTOM, status=ScheduledJobStatus.ENABLED,
        trigger=ScheduleTrigger(trigger_id="t1", trigger_type=ScheduleTriggerType.MANUAL, timezone="UTC")
    )

    now = datetime.utcnow()
    run = ScheduledJobRun(
        run_id="r1", job_id="j1", job_name="test", job_type=ScheduledJobType.CUSTOM,
        started_at=now - timedelta(minutes=5), status=ScheduledJobStatus.SUCCESS, decision=ScheduledJobDecision.RUN
    )

    # 30 min dedupe window -> should be duplicate
    assert deduper.is_duplicate_run(job, [run], 30) is True

    # 2 min dedupe window -> shouldn't be duplicate
    assert deduper.is_duplicate_run(job, [run], 2) is False
