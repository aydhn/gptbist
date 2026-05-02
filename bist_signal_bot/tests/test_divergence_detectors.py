import pytest
import pandas as pd
from datetime import datetime, timedelta
from bist_signal_bot.divergence.models import DivergenceRequest, DivergenceType, PivotMode, DivergenceStrength
from bist_signal_bot.divergence.pivots import PivotDetector
from bist_signal_bot.divergence.detectors import DivergenceDetector

@pytest.fixture
def synthetic_data():
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(20)]
    df = pd.DataFrame(index=dates)

    # Regular Bullish: Price lower low, RSI higher low
    df['close'] = [100, 90, 80, 85, 95, 85, 75, 85, 95, 100, 105, 110, 105, 100, 110, 120, 115, 125, 120, 115]
    df['rsi'] =   [50, 40, 30, 45, 60, 50, 40, 55, 65, 70,  75,  80,  70,  60,  75,  85,  75,  85,  80,  70]
    # Lows:
    # idx 2: close 80, rsi 30
    # idx 6: close 75 (LL), rsi 40 (HL) -> Regular Bullish

    # Highs:
    # idx 11: close 110, rsi 80
    # idx 15: close 120, rsi 85 (HH, HH - no divergence)
    # idx 17: close 125 (HH), rsi 85 (Equal/Lower high? wait let's make it lower)
    df.iloc[17, df.columns.get_loc('rsi')] = 75 # Lower high
    # Now idx 17: close 125 (HH), rsi 75 (LH) -> Regular Bearish

    return df

def test_divergence_detector_regular(synthetic_data):
    req = DivergenceRequest(indicators=["rsi"], min_pivot_distance=2, lookback=2)
    pivot_detector = PivotDetector(mode=PivotMode.LOOKBACK_ONLY, lookback=2)
    detector = DivergenceDetector(pivot_detector)

    df, events, issues = detector.detect_for_indicator(synthetic_data, "close", "rsi", req, "TEST", "1d")

    # Look for the Regular Bullish event around idx 6
    bullish_events = [e for e in events if e.divergence_type == DivergenceType.REGULAR_BULLISH]
    assert len(bullish_events) >= 1

    # Look for Regular Bearish event around idx 17
    bearish_events = [e for e in events if e.divergence_type == DivergenceType.REGULAR_BEARISH]
    assert len(bearish_events) >= 1

def test_divergence_detector_include_flags(synthetic_data):
    req = DivergenceRequest(indicators=["rsi"], min_pivot_distance=2, lookback=2, include_regular=False)
    pivot_detector = PivotDetector(mode=PivotMode.LOOKBACK_ONLY, lookback=2)
    detector = DivergenceDetector(pivot_detector)

    df, events, issues = detector.detect_for_indicator(synthetic_data, "close", "rsi", req, "TEST", "1d")

    # Since include_regular is False, we shouldn't get regular divergences
    regular_events = [e for e in events if e.divergence_type in (DivergenceType.REGULAR_BULLISH, DivergenceType.REGULAR_BEARISH)]
    assert len(regular_events) == 0

def test_strength_score():
    detector = DivergenceDetector(PivotDetector())
    # Strong divergence: big price diff, big indicator diff, close together
    score_strong = detector.calculate_strength(100, 80, 30, 50, 5, False)
    assert detector.classify_strength(score_strong) in (DivergenceStrength.MEDIUM, DivergenceStrength.STRONG)

def test_direction_score(synthetic_data):
    req = DivergenceRequest(indicators=["rsi"], min_pivot_distance=2, lookback=2)
    detector = DivergenceDetector(PivotDetector(lookback=2))
    df, _, _ = detector.detect_for_indicator(synthetic_data, "close", "rsi", req, "TEST", "1d")

    assert 'div_direction_score_rsi' in df.columns
    # Check that it takes 1.0 or -1.0 values
    assert df['div_direction_score_rsi'].isin([0.0, 1.0, -1.0]).all()
