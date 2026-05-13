import pytest
from datetime import datetime
from bist_signal_bot.runtime.models import (
    RuntimePipelineConfig, RuntimeScheduleConfig, RuntimeJobConfig,
    RuntimePipelineResult, RuntimeState, RuntimeJobType, RuntimeTrigger, RuntimePipelineStatus
)

def test_pipeline_config_defaults():
    config = RuntimePipelineConfig(strategy_name="test_strat")
    assert config.strategy_name == "test_strat"
    assert config.source == "mock"
    assert config.top_n == 10

def test_schedule_config_defaults():
    config = RuntimeScheduleConfig()
    assert config.interval_minutes == 60
    assert config.sleep_seconds == 5

def test_job_config_defaults():
    config = RuntimeJobConfig(job_type=RuntimeJobType.HEALTHCHECK)
    assert config.enabled is True
    assert config.max_retries == 1

def test_pipeline_result_summary():
    result = RuntimePipelineResult(
        run_id="run-1",
        trigger=RuntimeTrigger.TEST,
        config=RuntimePipelineConfig(strategy_name="test_strat"),
        status=RuntimePipelineStatus.SUCCESS,
        started_at=datetime.utcnow()
    )
    summary = result.summary()
    assert summary["run_id"] == "run-1"
    assert summary["status"] == "SUCCESS"
    assert summary["jobs_total"] == 0

def test_state_summary():
    state = RuntimeState()
    summary = state.summary()
    assert summary["total_runs"] == 0
    assert summary["consecutive_failures"] == 0
