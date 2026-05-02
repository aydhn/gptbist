import pytest
import pandas as pd
import numpy as np
from bist_signal_bot.patterns.candles import (
    CandleBodyMetricsDetector, DojiDetector, HammerDetector, EngulfingDetector,
    InsideOutsideBarDetector, MarubozuDetector, CandleCompositeDetector
)
from bist_signal_bot.core.exceptions import PatternValidationError

@pytest.fixture
def sample_data():
    return pd.DataFrame({
        "open": [100, 105, 110, 115, 110],
        "high": [105, 110, 112, 120, 115],
        "low": [95, 100, 108, 110, 105],
        "close": [105, 105, 109, 110, 112] # row 1: doji, row 4: inside bar approx
    })

def test_candle_body_metrics(sample_data):
    det = CandleBodyMetricsDetector()
    res = det(sample_data)
    assert "candle_body_pct" in res.columns
    assert "candle_direction" in res.columns
    assert not res.isna().all().all()

def test_doji_detector(sample_data):
    det = DojiDetector()
    res = det(sample_data, body_threshold=0.1)
    col = "candle_doji_0.1"
    assert col in res.columns
    assert res[col].iloc[1] == 1.0 # open 105, close 105 -> body 0 -> doji

def test_hammer_approximation(sample_data):
    det = HammerDetector()
    res = det(sample_data, **det.spec.default_params)
    assert "candle_hammer" in res.columns
    assert "candle_inverted_hammer" in res.columns

def test_engulfing_detector(sample_data):
    det = EngulfingDetector()
    res = det(sample_data)
    assert "bullish_engulfing" in res.columns
    assert "bearish_engulfing" in res.columns

def test_inside_outside_bar(sample_data):
    det = InsideOutsideBarDetector()
    res = det(sample_data)
    assert "inside_bar" in res.columns
    assert "outside_bar" in res.columns

def test_marubozu_approximation(sample_data):
    det = MarubozuDetector()
    res = det(sample_data, **det.spec.default_params)
    assert "bullish_marubozu" in res.columns

def test_candle_composite(sample_data):
    det = CandleCompositeDetector()
    res = det(sample_data)
    assert "candle_pattern_score" in res.columns
    assert res["candle_pattern_score"].max() <= 100
    assert res["candle_pattern_score"].min() >= -100

def test_missing_columns(sample_data):
    det = CandleBodyMetricsDetector()
    bad_data = sample_data.drop(columns=["open"])
    with pytest.raises(PatternValidationError):
        det(bad_data)
