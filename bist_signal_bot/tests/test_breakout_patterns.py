import pytest
import pandas as pd
import numpy as np
from bist_signal_bot.patterns.breakouts import (
    PriceBreakoutDetector, VolumeConfirmedBreakoutDetector,
    LaggedFalseBreakoutDetector, BreakoutRetestDetector,
    GapBreakoutDetector, BreakoutCompositeDetector
)

@pytest.fixture
def sample_data():
    np.random.seed(42)
    return pd.DataFrame({
        "open": np.random.uniform(100, 110, 50),
        "high": np.random.uniform(105, 115, 50),
        "low": np.random.uniform(95, 105, 50),
        "close": np.random.uniform(100, 110, 50),
        "volume": np.random.uniform(1000, 5000, 50)
    })

def test_price_breakout(sample_data):
    det = PriceBreakoutDetector()
    res = det(sample_data, window=10)
    assert "price_breakout_up_10" in res.columns
    assert "price_breakout_down_10" in res.columns

def test_volume_confirmed_breakout(sample_data):
    det = VolumeConfirmedBreakoutDetector()
    res = det(sample_data, price_window=10, volume_window=10, volume_multiplier=1.5)
    assert "volume_confirmed_breakout_up_10_10" in res.columns

def test_lagged_false_breakout(sample_data):
    det = LaggedFalseBreakoutDetector()
    res = det(sample_data, window=10, fail_within_bars=3)
    assert "false_breakout_up_lagged_10_3" in res.columns

def test_gap_breakout(sample_data):
    det = GapBreakoutDetector()
    res = det(sample_data, gap_threshold=0.02)
    assert "gap_up_0.02" in res.columns

def test_breakout_composite(sample_data):
    det = BreakoutCompositeDetector()
    res = det(sample_data, price_window=10, volume_window=10)
    assert "breakout_pressure_score" in res.columns
    assert "breakout_direction_score" in res.columns
    assert res["breakout_pressure_score"].max() <= 100
    assert res["breakout_direction_score"].min() >= -100
