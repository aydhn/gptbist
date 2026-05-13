import pytest
from datetime import datetime
from bist_signal_bot.runtime.scheduler import RuntimeScheduler
from bist_signal_bot.runtime.models import RuntimeScheduleConfig, RuntimePipelineConfig

class MockOrchestrator:
    def __init__(self):
        self.runs = 0
        from bist_signal_bot.runtime.models import RuntimePipelineResult, RuntimeTrigger, RuntimePipelineStatus
        self.result_class = RuntimePipelineResult
        self.trigger_class = RuntimeTrigger
        self.status_class = RuntimePipelineStatus

    def run_once(self, config):
        self.runs += 1
        return self.result_class(
            run_id=f"run-{self.runs}",
            trigger=self.trigger_class.TEST,
            config=config,
            status=self.status_class.SUCCESS,
            started_at=datetime.utcnow()
        )


def test_scheduler_max_iterations(monkeypatch):
    import time
    monkeypatch.setattr(time, "sleep", lambda x: None)

    orchestrator = MockOrchestrator()
    scheduler = RuntimeScheduler(orchestrator)

    sched_cfg = RuntimeScheduleConfig(interval_minutes=60, max_iterations=2, sleep_seconds=1, run_immediately=True)
    pipe_cfg = RuntimePipelineConfig(strategy_name="test")

    # We must explicitly force time check to True to avoid actual wait
    monkeypatch.setattr(scheduler, "should_run_now", lambda *args, **kwargs: True)

    results = scheduler.run_loop(sched_cfg, pipe_cfg)
    assert len(results) == 2
    assert orchestrator.runs == 2
def test_scheduler_next_run_time():
    scheduler = RuntimeScheduler(None)
    now = datetime(2023, 1, 1, 12, 0, 0)
    next_time = scheduler.next_run_time(now, interval_minutes=60)
    assert next_time == datetime(2023, 1, 1, 13, 0, 0)
