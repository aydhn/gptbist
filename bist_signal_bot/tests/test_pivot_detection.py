import pytest
import pandas as pd
from datetime import datetime, timedelta
from bist_signal_bot.divergence.models import PivotMode, PivotType
from bist_signal_bot.divergence.pivots import PivotDetector

@pytest.fixture
def sample_series():
    # Simple wave
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(10)]
    values = [10, 12, 15, 11, 9, 8, 14, 18, 16, 15]
    # high at idx 2 (val 15), low at idx 5 (val 8), high at idx 7 (val 18)
    return pd.Series(values, index=dates)

def test_pivot_detector_lookback_only_high(sample_series):
    detector = PivotDetector(mode=PivotMode.LOOKBACK_ONLY, lookback=3)
    pivots = detector.detect_pivots(sample_series, PivotType.HIGH)

    # Check that it detected a high
    assert (pivots == 1).any()
    points = detector.extract_pivot_points(sample_series, PivotType.HIGH, pivots)
    assert len(points) > 0
    assert not points[0].confirmed

    # In LOOKBACK_ONLY, future bar shouldn't be used, so a new high is immediately marked if > prev rolling max

def test_pivot_detector_lookback_only_low(sample_series):
    detector = PivotDetector(mode=PivotMode.LOOKBACK_ONLY, lookback=3)
    pivots = detector.detect_pivots(sample_series, PivotType.LOW)
    assert (pivots == 1).any()

def test_pivot_detector_confirmed_lagged(sample_series):
    detector = PivotDetector(mode=PivotMode.CONFIRMED_LAGGED, lookback=2, confirmation_bars=2)
    pivots = detector.detect_pivots(sample_series, PivotType.HIGH)

    # Feature should be shifted by confirmation bars
    points = detector.extract_pivot_points(sample_series, PivotType.HIGH, pivots)

    # If there are any, their real timestamp should be 'confirmation_bars' before their detection index
    for p in points:
        assert p.confirmed
        assert p.confirmation_lag == 2

def test_extract_pivot_points(sample_series):
    detector = PivotDetector(mode=PivotMode.LOOKBACK_ONLY, lookback=2)
    flags = pd.Series([0, 0, 1, 0, 0], index=sample_series.index[:5])
    points = detector.extract_pivot_points(sample_series, PivotType.HIGH, flags)

    assert len(points) == 1
    assert points[0].index_position == 2
    assert points[0].value == 15
