import pytest
from datetime import datetime, timedelta
from bist_signal_bot.research_lab.deduplication import ResearchJobDeduplicator
from bist_signal_bot.research_lab.models import ResearchJob, ResearchJobType, ResearchJobPriority, ResearchJobTrigger, ResearchJobStatus

def test_deduplicator_same_key():
    deduper = ResearchJobDeduplicator()
    j1 = ResearchJob(job_id="1", job_type=ResearchJobType.BACKTEST, title="A", symbols=["X"], strategy_name="S")
    j2 = ResearchJob(job_id="2", job_type=ResearchJobType.BACKTEST, title="B", symbols=["X"], strategy_name="S")

    assert deduper.build_dedupe_key(j1) == deduper.build_dedupe_key(j2)

def test_deduplicator_window():
    deduper = ResearchJobDeduplicator()
    j1 = ResearchJob(job_id="1", job_type=ResearchJobType.BACKTEST, title="A", symbols=["X"])
    j1.created_at = datetime.utcnow()
    j1.status = ResearchJobStatus.QUEUED
    j1.dedupe_key = deduper.build_dedupe_key(j1)

    j2 = ResearchJob(job_id="2", job_type=ResearchJobType.BACKTEST, title="B", symbols=["X"])

    # Existing job is queued within window, should be duplicate
    assert deduper.is_duplicate(j2, [j1], 24) is True

    # If existing job is old, not a duplicate
    j1.created_at = datetime.utcnow() - timedelta(hours=25)
    assert deduper.is_duplicate(j2, [j1], 24) is False
