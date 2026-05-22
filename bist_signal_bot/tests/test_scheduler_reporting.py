import pytest
from datetime import datetime
from bist_signal_bot.scheduler.reporting import format_schedule_list_text
from bist_signal_bot.scheduler.models import ScheduledJob, ScheduledJobType, ScheduledJobStatus, ScheduleTrigger, ScheduleTriggerType

def test_reporting_schedule_list():
    job = ScheduledJob(
        job_id="j1", name="test", job_type=ScheduledJobType.HEALTHCHECK, status=ScheduledJobStatus.ENABLED,
        trigger=ScheduleTrigger(trigger_id="t1", trigger_type=ScheduleTriggerType.DAILY, timezone="UTC")
    )
    text = format_schedule_list_text([job])
    assert "j1" in text
    assert "test" in text
    assert "ENABLED" in text
    assert "DAILY" in text
