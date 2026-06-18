import pytest
from bist_signal_bot.stress.storage import StressStore
from bist_signal_bot.stress.models import StressTestResult, StressTestRequest, StressInputType, StressStatus, StressSeverity, MonteCarloConfig, MonteCarloMethod
import uuid

def test_stress_storage(tmp_path):
    store = StressStore(base_dir=tmp_path)

    req = StressTestRequest(
        input_type=StressInputType.CUSTOM_RETURNS,
        monte_carlo_config=MonteCarloConfig(
            method=MonteCarloMethod.BOOTSTRAP, simulations=10, horizon_days=5, seed=42, initial_value=100.0
        ),
        ruin_threshold_pct=30.0
    )

    stress_id = str(uuid.uuid4())
    res = StressTestResult(
        stress_id=stress_id,
        request=req,
        status=StressStatus.PASS,
        stress_rating=StressSeverity.LOW
    )

    paths = store.save_result(res)
    assert "result_json" in paths

    loaded = store.load_result(stress_id)
    assert loaded is not None
    assert loaded.stress_id == stress_id

    latest = store.load_latest_result()
    assert latest is not None
    assert latest.stress_id == stress_id

import json
from pathlib import Path
from unittest.mock import patch
from bist_signal_bot.core.exceptions import StressStorageError

def test_stress_storage_init_error():
    """Test fallback when get_stress_dir fails."""
    with patch("bist_signal_bot.stress.storage.get_stress_dir", side_effect=Exception("Mocked error")):
        store = StressStore()
        assert store.base_path == Path("data/stress")

def test_stress_storage_save_error(tmp_path):
    """Test exception raising during save_result."""
    store = StressStore(base_dir=tmp_path)

    req = StressTestRequest(
        input_type=StressInputType.CUSTOM_RETURNS,
        monte_carlo_config=MonteCarloConfig(
            method=MonteCarloMethod.BOOTSTRAP, simulations=10, horizon_days=5, seed=42, initial_value=100.0
        ),
        ruin_threshold_pct=30.0
    )

    stress_id = str(uuid.uuid4())
    res = StressTestResult(
        stress_id=stress_id,
        request=req,
        status=StressStatus.PASS,
        stress_rating=StressSeverity.LOW
    )

    with patch("bist_signal_bot.stress.storage.open", side_effect=IOError("Disk full")):
        with pytest.raises(StressStorageError, match="Save failed: Disk full"):
            store.save_result(res)

def test_stress_storage_load_error(tmp_path):
    """Test exception handling during load_result and load_latest_result with invalid JSON."""
    store = StressStore(base_dir=tmp_path)
    stress_id = "test-error-123"

    # Create the directory structure and an invalid JSON file
    date_str = "20240101"
    result_dir = store.base_path / "results" / date_str / stress_id
    result_dir.mkdir(parents=True, exist_ok=True)
    json_file = result_dir / "stress_result.json"

    with open(json_file, "w") as f:
        f.write("invalid json")

    loaded = store.load_result(stress_id)
    assert loaded is None

    latest = store.load_latest_result()
    assert latest is None

def test_stress_storage_list_recent_error(tmp_path):
    """Test that list_recent_results gracefully ignores unparseable results."""
    store = StressStore(base_dir=tmp_path)

    # Valid result
    stress_id_valid = "valid-123"
    result_dir_valid = store.base_path / "results" / "20240101" / stress_id_valid
    result_dir_valid.mkdir(parents=True, exist_ok=True)
    with open(result_dir_valid / "stress_result.json", "w") as f:
        json.dump({
            "stress_id": stress_id_valid,
            "stress_rating": "LOW",
            "status": "PASS"
        }, f)

    # Invalid result
    stress_id_invalid = "invalid-123"
    result_dir_invalid = store.base_path / "results" / "20240101" / stress_id_invalid
    result_dir_invalid.mkdir(parents=True, exist_ok=True)
    with open(result_dir_invalid / "stress_result.json", "w") as f:
        f.write("bad data")

    recent = store.list_recent_results()
    assert len(recent) == 1
    assert recent[0]["stress_id"] == stress_id_valid
