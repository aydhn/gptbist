import pytest
from datetime import datetime
from bist_signal_bot.runtime.state import RuntimeStateStore
from bist_signal_bot.runtime.models import RuntimePipelineResult, RuntimePipelineConfig, RuntimeTrigger, RuntimePipelineStatus

def test_state_store_save_load(tmp_path):
    store = RuntimeStateStore(base_dir=tmp_path)
    state = store.load()
    assert state.total_runs == 0

    state.total_runs = 5
    store.save(state)

    state2 = store.load()
    assert state2.total_runs == 5

def test_state_store_mark_running_finished(tmp_path):
    store = RuntimeStateStore(base_dir=tmp_path)
    store.mark_running("run-1", "lock-1")

    state = store.load()
    assert state.is_running
    assert state.last_run_id == "run-1"

    result = RuntimePipelineResult(
        run_id="run-1",
        trigger=RuntimeTrigger.TEST,
        config=RuntimePipelineConfig(strategy_name="test"),
        status=RuntimePipelineStatus.SUCCESS,
        started_at=datetime.utcnow()
    )

    store.mark_finished(result)
    state = store.load()
    assert not state.is_running
    assert state.total_runs == 1
    assert state.success_runs == 1
