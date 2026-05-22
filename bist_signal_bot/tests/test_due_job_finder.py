import pytest
from datetime import datetime
from bist_signal_bot.scheduler.due import DueJobFinder
from bist_signal_bot.scheduler.triggers import ScheduleTriggerEvaluator
from bist_signal_bot.scheduler.session import MarketSessionResolver
from bist_signal_bot.scheduler.calendar import BISTMarketCalendar
from bist_signal_bot.scheduler.models import (
    ScheduledJob, ScheduleTrigger, ScheduleTriggerType, ScheduledJobType, ScheduledJobStatus, ScheduledJobDecision
)

class MockSettings:
    pass

def test_due_job_finder_disabled_skipped(tmp_path):
    cal = BISTMarketCalendar(data_dir=tmp_path)
    res = MarketSessionResolver(cal, MockSettings())
    ev = ScheduleTriggerEvaluator()
    finder = DueJobFinder(ev, res)

    job = ScheduledJob(
        job_id="j1", name="test", job_type=ScheduledJobType.CUSTOM, status=ScheduledJobStatus.DISABLED, enabled=False,
        trigger=ScheduleTrigger(trigger_id="t1", trigger_type=ScheduleTriggerType.MANUAL, timezone="UTC")
    )

    dt = datetime(2025, 10, 24, 12, 0)
    result = finder.find_due_jobs([job], dt)

    assert len(result.due_jobs) == 0
    assert len(result.skipped_jobs) == 1

    decision, _ = finder.classify_job(job, dt, result.session_snapshot)
    assert decision == ScheduledJobDecision.SKIP_DISABLED
