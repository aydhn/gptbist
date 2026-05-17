import pytest
from pathlib import Path
from bist_signal_bot.scenarios.storage import ScenarioStore
from bist_signal_bot.scenarios.models import ScenarioResult, ScenarioConfig, ScenarioType, ScenarioStatus

@pytest.fixture
def dummy_result():
    config = ScenarioConfig(
        scenario_id="test-scenario",
        name="Test",
        scenario_type=ScenarioType.CUSTOM,
        description="test",
        symbols=["ASELS"]
    )
    return ScenarioResult(
        run_id="run-123",
        scenario=config,
        status=ScenarioStatus.SUCCESS
    )

def test_store_paths(tmp_path):
    store = ScenarioStore(base_dir=tmp_path)
    assert store.get_scenarios_dir() == tmp_path / "scenarios"
    assert store.get_scenario_runs_dir() == tmp_path / "scenarios" / "runs"
    assert store.get_golden_dir() == tmp_path / "scenarios" / "golden"

def test_save_and_load_result(tmp_path, dummy_result):
    store = ScenarioStore(base_dir=tmp_path)

    paths = store.save_result(dummy_result)
    assert "json" in paths
    assert paths["json"].exists()

    loaded = store.load_result("run-123")
    assert loaded is not None
    assert loaded.run_id == "run-123"
    assert loaded.status == ScenarioStatus.SUCCESS

def test_list_recent_runs(tmp_path, dummy_result):
    store = ScenarioStore(base_dir=tmp_path)
    store.save_result(dummy_result)

    recent = store.list_recent_runs()
    assert len(recent) == 1
    assert recent[0]["run_id"] == "run-123"
    assert recent[0]["scenario_id"] == "test-scenario"
    assert recent[0]["status"] == "SUCCESS"
