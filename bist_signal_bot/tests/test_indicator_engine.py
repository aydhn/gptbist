import pytest
import pandas as pd
import numpy as np
from bist_signal_bot.indicators.engine import IndicatorEngine
from bist_signal_bot.indicators.registry import IndicatorRegistry
from bist_signal_bot.indicators.models import IndicatorRequest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import IndicatorCalculationError, IndicatorValidationError

@pytest.fixture
def sample_data():
    dates = pd.date_range("2024-01-01", periods=100)
    return pd.DataFrame({
        "open": np.random.rand(100) * 100,
        "high": np.random.rand(100) * 100,
        "low": np.random.rand(100) * 100,
        "close": np.random.rand(100) * 100,
        "volume": np.random.randint(1000, 5000, 100)
    }, index=dates)

@pytest.fixture
def engine():
    return IndicatorEngine(settings=Settings(INDICATOR_CONTINUE_ON_ERROR=True))

def test_engine_single_calc(engine, sample_data):
    req = IndicatorRequest(name="sma", params={"window": 10})
    df, result = engine.calculate(sample_data, req)

    assert result.status == "SUCCESS"
    assert "sma_10" in result.output_columns
    assert "sma_10" in df.columns
    # Ensure original is not mutated
    assert "sma_10" not in sample_data.columns

def test_engine_batch_calc(engine, sample_data):
    reqs = [
        IndicatorRequest(name="sma", params={"window": 10}),
        IndicatorRequest(name="ema", params={"span": 20})
    ]
    batch = engine.calculate_many(sample_data, reqs)

    assert batch.requested_count == 2
    assert batch.success_count == 2
    assert "sma_10" in batch.output_data.columns
    assert "ema_20" in batch.output_data.columns

def test_engine_continue_on_error(sample_data):
    # Engine with continue_on_error = True
    engine = IndicatorEngine(settings=Settings(INDICATOR_CONTINUE_ON_ERROR=True))

    reqs = [
        IndicatorRequest(name="sma", params={"window": -5}), # Invalid param, will fail
        IndicatorRequest(name="ema", params={"span": 20}) # Will succeed
    ]
    batch = engine.calculate_many(sample_data, reqs, continue_on_error=True)

    assert batch.requested_count == 2
    assert batch.success_count == 1
    assert batch.failed_count == 1
    assert "ema_20" in batch.output_data.columns

def test_engine_fail_on_error(sample_data):
    engine = IndicatorEngine(settings=Settings(INDICATOR_CONTINUE_ON_ERROR=False))

    reqs = [
        IndicatorRequest(name="sma", params={"window": -5}), # Invalid param
    ]
    with pytest.raises(IndicatorValidationError):
        engine.calculate_many(sample_data, reqs, continue_on_error=False)

def test_engine_parse_requests(engine):
    raw = ["sma:window=20", "macd:fast=12,slow=26,signal=9", "rsi"]
    reqs = engine.parse_requests(raw)

    assert len(reqs) == 3
    assert reqs[0].name == "sma"
    assert reqs[0].params == {"window": 20}
    assert reqs[1].name == "macd"
    assert reqs[1].params == {"fast": 12, "slow": 26, "signal": 9}
    assert reqs[2].name == "rsi"
    assert reqs[2].params == {}

def test_engine_default_set(engine, sample_data):
    batch = engine.calculate_default_set(sample_data)
    assert batch.success_count >= 10
    assert "sma_20" in batch.output_data.columns
