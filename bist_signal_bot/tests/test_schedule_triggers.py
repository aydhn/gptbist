import pytest
from datetime import datetime
from bist_signal_bot.scheduler.triggers import ScheduleTriggerEvaluator
from bist_signal_bot.scheduler.models import (
    ScheduledJob, ScheduleTrigger, ScheduleTriggerType, ScheduledJobType, ScheduledJobStatus,
    MarketSessionSnapshot, MarketSessionType, MarketDayType
)

def test_trigger_evaluator_disabled():
    evaluator = ScheduleTriggerEvaluator()
    job = ScheduledJob(
        job_id="j1", name="test", job_type=ScheduledJobType.CUSTOM, status=ScheduledJobStatus.DISABLED, enabled=False,
        trigger=ScheduleTrigger(trigger_id="t1", trigger_type=ScheduleTriggerType.MANUAL, timezone="UTC")
    )
    snap = MarketSessionSnapshot(generated_at=datetime.utcnow(), local_date=datetime.utcnow(), timezone="UTC", day_type=MarketDayType.TRADING_DAY, session_type=MarketSessionType.INTRADAY, market_open=True)

    is_due, reason = evaluator.is_due(job, datetime.utcnow(), snap)
    assert is_due is False
    assert "disabled" in reason

def test_trigger_evaluator_daily():
    evaluator = ScheduleTriggerEvaluator()
    job = ScheduledJob(
        job_id="j1", name="test", job_type=ScheduledJobType.CUSTOM, status=ScheduledJobStatus.ENABLED,
        trigger=ScheduleTrigger(trigger_id="t1", trigger_type=ScheduleTriggerType.DAILY, timezone="UTC", hour=10, minute=30)
    )
    snap = MarketSessionSnapshot(generated_at=datetime.utcnow(), local_date=datetime.utcnow(), timezone="UTC", day_type=MarketDayType.TRADING_DAY, session_type=MarketSessionType.INTRADAY, market_open=True)

    dt = datetime(2025, 1, 1, 10, 30)
    is_due, _ = evaluator.is_due(job, dt, snap)
    assert is_due is True

    dt2 = datetime(2025, 1, 1, 10, 31)
    is_due, _ = evaluator.is_due(job, dt2, snap)
    assert is_due is True # grace period

    dt3 = datetime(2025, 1, 1, 11, 00)
    is_due, _ = evaluator.is_due(job, dt3, snap)
    assert is_due is False
