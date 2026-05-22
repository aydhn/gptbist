import pytest
from datetime import datetime
from pydantic import ValidationError
from bist_signal_bot.scheduler.models import (
    ScheduleTrigger,
    ScheduleTriggerType,
    ScheduledJob,
    ScheduledJobType,
    ScheduledJobStatus,
    MarketSessionType
)

def test_trigger_validation():
    with pytest.raises(ValueError, match="timezone cannot be empty"):
        ScheduleTrigger(trigger_id="t1", trigger_type=ScheduleTriggerType.DAILY, timezone="")

    with pytest.raises(ValidationError):
        ScheduleTrigger(trigger_id="t1", trigger_type=ScheduleTriggerType.DAILY, timezone="UTC", hour=25)

    t = ScheduleTrigger(trigger_id="t1", trigger_type=ScheduleTriggerType.DAILY, timezone="UTC", hour=10, minute=30)
    assert t.hour == 10
    assert t.minute == 30

def test_job_validation():
    with pytest.raises(ValueError, match="name cannot be empty"):
        ScheduledJob(
            job_id="j1",
            name="",
            job_type=ScheduledJobType.HEALTHCHECK,
            status=ScheduledJobStatus.ENABLED,
            trigger=ScheduleTrigger(trigger_id="t1", trigger_type=ScheduleTriggerType.MANUAL, timezone="UTC")
        )
