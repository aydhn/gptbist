import pytest
from datetime import datetime
from bist_signal_bot.scheduler.storage import SchedulerStore
from bist_signal_bot.scheduler.models import ScheduledJob, ScheduledJobType, ScheduledJobStatus, ScheduleTrigger, ScheduleTriggerType, MarketSessionType

def test_storage_save_load_job(tmp_path):
    store = SchedulerStore(data_dir=tmp_path)
    job = ScheduledJob(
        job_id="j1", name="test", job_type=ScheduledJobType.HEALTHCHECK, status=ScheduledJobStatus.ENABLED,
        trigger=ScheduleTrigger(trigger_id="t1", trigger_type=ScheduleTriggerType.MARKET_SESSION, timezone="UTC", market_sessions=[MarketSessionType.INTRADAY])
    )

    store.save_job(job)
    loaded = store.load_jobs()

    assert len(loaded) == 1
    assert loaded[0].job_id == "j1"
    assert loaded[0].trigger.market_sessions[0] == MarketSessionType.INTRADAY
