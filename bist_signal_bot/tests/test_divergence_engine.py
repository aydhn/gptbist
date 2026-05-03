import pytest
import pandas as pd
from datetime import datetime, timedelta
from bist_signal_bot.divergence.engine import DivergenceEngine
from bist_signal_bot.config.settings import Settings

@pytest.fixture
def test_data():
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(150)] # Give it 150 rows so it doesn't fail the 120 min requirement
    df = pd.DataFrame(index=dates)
    df['close'] = [100 + i for i in range(150)]
    df['high'] = df['close'] + 2
    df['low'] = df['close'] - 2
    df['open'] = df['close']
    df['volume'] = [1000] * 150
    return df

def test_divergence_engine_ensure_indicator(test_data):
    engine = DivergenceEngine()
    df = engine.ensure_indicator_columns(test_data, ["rsi"])
    assert "rsi" in df.columns
    assert "rsi_14" in df.columns

def test_divergence_engine_detect(test_data):
    engine = DivergenceEngine()
    req = engine.parse_request(indicators=["rsi"])
    result = engine.detect(test_data, req, symbol="TEST", timeframe="1d")

    assert result.result.symbol == "TEST"
    assert result.result.timeframe == "1d"
    assert "div_direction_score_rsi" in result.output_data.columns

def test_divergence_engine_invalid_indicator(test_data):
    engine = DivergenceEngine()
    req = engine.parse_request(indicators=["unknown_ind_123"])
    result = engine.detect(test_data, req)

    assert len(result.result.issues) > 0
    assert result.result.status.value in ["WARNING", "FAILED"]

def test_divergence_engine_default_set(test_data):
    engine = DivergenceEngine()
    result = engine.detect_default_set(test_data)
    assert len(result.result.requested_indicators) > 0

    for ind in result.result.requested_indicators:
        assert f"div_direction_score_{ind}" in result.output_data.columns
