import pytest
from pathlib import Path
import json
from datetime import datetime

from bist_signal_bot.optimization.storage import OptimizationResultStore
from bist_signal_bot.optimization.models import (
    OptimizationResult, OptimizationConfig, OptimizationMethod, ObjectiveMetric, OptimizationStatus, OptimizationTrial
)
from bist_signal_bot.config.settings import Settings

def test_storage_save_json(tmp_path):
    settings = Settings()
    # Mock settings to point to tmp_path
    class MockSettings(Settings):
        DATA_DIR: str = str(tmp_path)

    store = OptimizationResultStore(settings=MockSettings())
    res = OptimizationResult(
        strategy_name="test", symbol="TST", method=OptimizationMethod.GRID_SEARCH,
        objective=ObjectiveMetric.TOTAL_RETURN, config=OptimizationConfig(),
        search_spaces=[], status=OptimizationStatus.SUCCESS,
        started_at=datetime.utcnow(), finished_at=datetime.utcnow()
    )

    path = store.save_json(res)
    assert path.exists()
    with open(path) as f:
        data = json.load(f)
        assert data["summary"]["strategy"] == "test"

def test_storage_save_csv(tmp_path):
    class MockSettings(Settings):
        DATA_DIR: str = str(tmp_path)

    store = OptimizationResultStore(settings=MockSettings())
    t1 = OptimizationTrial(trial_id=1, params={"a":1}, status=OptimizationStatus.SUCCESS)
    res = OptimizationResult(
        strategy_name="test", symbol="TST", method=OptimizationMethod.GRID_SEARCH,
        objective=ObjectiveMetric.TOTAL_RETURN, config=OptimizationConfig(),
        search_spaces=[], status=OptimizationStatus.SUCCESS, trials=[t1],
        started_at=datetime.utcnow(), finished_at=datetime.utcnow()
    )

    path = store.save_trials_csv(res)
    assert path.exists()
    content = path.read_text()
    assert "trial_id" in content
    assert "status" in content
