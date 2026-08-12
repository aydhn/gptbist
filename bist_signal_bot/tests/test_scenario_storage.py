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

def test_list_recent_runs_early_break(tmp_path, dummy_result):
    import time
    from datetime import datetime, timedelta, UTC
    import json

    store = ScenarioStore(base_dir=tmp_path)

    # Create multiple runs to test the limit early break
    for i in range(25):
        run_id = f"run-{i}"
        d = datetime.now(UTC) - timedelta(days=i%5) # Spread across 5 days
        date_str = d.strftime("%Y%m%d")

        dir_path = store.get_scenario_runs_dir() / date_str / run_id
        dir_path.mkdir(parents=True, exist_ok=True)
        json_path = dir_path / "scenario_result.json"

        # Override dummy result run_id and dates
        dummy_result.run_id = run_id
        dummy_result.started_at = d

        with open(json_path, "w") as f:
            json.dump(dummy_result.model_dump(mode="json"), f)

    # Default limit is 20
    recent = store.list_recent_runs(limit=5)
    assert len(recent) == 5

    recent_all = store.list_recent_runs(limit=50)
    assert len(recent_all) == 25
