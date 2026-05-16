import pytest
from pathlib import Path
from bist_signal_bot.scenarios.golden import GoldenSnapshotManager
from bist_signal_bot.scenarios.models import ScenarioResult, ScenarioConfig, ScenarioType, ScenarioStatus
from bist_signal_bot.core.exceptions import GoldenRegressionError

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
        status=ScenarioStatus.SUCCESS,
        elapsed_seconds=10.5
    )

def test_save_and_load_snapshot(tmp_path, dummy_result):
    manager = GoldenSnapshotManager(tmp_path)

    # Must raise without confirm
    with pytest.raises(GoldenRegressionError):
        manager.save_snapshot(dummy_result, confirm=False)

    snap = manager.save_snapshot(dummy_result, confirm=True)
    assert snap is not None

    loaded = manager.load_snapshot("test-scenario")
    assert loaded is not None
    assert loaded.snapshot_id == snap.snapshot_id
    assert loaded.scenario_id == "test-scenario"

def test_normalize_removes_variable_fields(tmp_path, dummy_result):
    manager = GoldenSnapshotManager(tmp_path)
    norm = manager.normalize_result(dummy_result)

    assert "elapsed_seconds" not in norm
    assert "started_at" not in norm
    assert "run_id" not in norm
    assert norm["status"] == "SUCCESS"

def test_compare_snapshots(tmp_path, dummy_result):
    manager = GoldenSnapshotManager(tmp_path)
    manager.save_snapshot(dummy_result, confirm=True)

    comp = manager.compare_to_snapshot(dummy_result)
    assert comp.matched is True
    assert comp.status == ScenarioStatus.SUCCESS
    assert len(comp.differences) == 0

    # Change status to trigger diff
    dummy_result.status = ScenarioStatus.FAILED
    comp2 = manager.compare_to_snapshot(dummy_result)
    assert comp2.matched is False
    assert comp2.status == ScenarioStatus.FAILED
    assert len(comp2.differences) > 0
