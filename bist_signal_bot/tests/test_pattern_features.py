import pytest
import pandas as pd
import numpy as np
from bist_signal_bot.features.pattern_features import PatternFeatureBuilder
from bist_signal_bot.config.settings import Settings

@pytest.fixture
def sample_data():
    np.random.seed(42)
    return pd.DataFrame({
        "open": np.random.uniform(100, 110, 100),
        "high": np.random.uniform(105, 115, 100),
        "low": np.random.uniform(95, 105, 100),
        "close": np.random.uniform(100, 110, 100),
        "volume": np.random.uniform(1000, 5000, 100)
    })

def test_pattern_feature_builder_basic(sample_data):
    settings = Settings()
    builder = PatternFeatureBuilder(settings=settings)
    res = builder.build_basic_pattern_features(sample_data)

    assert res.success_count > 0
    assert "candle_body_pct" in res.output_data.columns
    assert f"price_breakout_up_{settings.PATTERN_BREAKOUT_WINDOW}" in res.output_data.columns

def test_pattern_feature_builder_advanced(sample_data):
    settings = Settings()
    builder = PatternFeatureBuilder(settings=settings)
    res = builder.build_advanced_pattern_features(sample_data)

    assert res.success_count > 0
    assert "bullish_engulfing" in res.output_data.columns
    assert "pivot_point" in res.output_data.columns

def test_pattern_feature_builder_full(sample_data):
    settings = Settings()
    builder = PatternFeatureBuilder(settings=settings)
    res = builder.build_full_pattern_features(sample_data)

    assert res.success_count > 0
    assert "candle_body_pct" in res.output_data.columns
    assert "pivot_point" in res.output_data.columns
