import pytest
import pandas as pd
import numpy as np
from bist_signal_bot.patterns.support_resistance import (
    RollingSupportResistanceDetector, PivotPointsDetector,
    SRTouchCountDetector, NearSRDetector, SRCompositeDetector
)

@pytest.fixture
def sample_data():
    np.random.seed(42)
    return pd.DataFrame({
        "open": np.random.uniform(100, 110, 50),
        "high": np.random.uniform(105, 115, 50),
        "low": np.random.uniform(95, 105, 50),
        "close": np.random.uniform(100, 110, 50)
    })

def test_rolling_sr(sample_data):
    det = RollingSupportResistanceDetector()
    res = det(sample_data, window=20)
    assert "rolling_resistance_20" in res.columns
    assert "rolling_support_20" in res.columns

def test_pivot_points(sample_data):
    det = PivotPointsDetector()
    res = det(sample_data)
    assert "pivot_point" in res.columns
    assert "pivot_r1" in res.columns

def test_sr_touch_count(sample_data):
    det = SRTouchCountDetector()
    res = det(sample_data, window=20, tolerance_pct=0.01)
    assert "resistance_touch_count_20" in res.columns
    assert "support_touch_count_20" in res.columns

def test_near_sr(sample_data):
    det = NearSRDetector()
    res = det(sample_data, window=20, tolerance_pct=0.02)
    assert "near_resistance_20" in res.columns

def test_sr_composite(sample_data):
    det = SRCompositeDetector()
    res = det(sample_data, window=20)
    assert "sr_position_score" in res.columns
    assert "sr_pressure_score" in res.columns
