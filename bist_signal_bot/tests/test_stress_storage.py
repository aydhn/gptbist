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
