import pytest
import pandas as pd
import numpy as np

from bist_signal_bot.features.momentum_features import MomentumFeatureBuilder
from bist_signal_bot.indicators.engine import IndicatorEngine
from bist_signal_bot.config.settings import Settings

@pytest.fixture
def sample_data():
    dates = pd.date_range("2024-01-01", periods=100)
    close = np.linspace(100, 200, 100)
    high = close + 5
    low = close - 5
    volume = np.random.randint(1000, 5000, 100)
    return pd.DataFrame({
        "open": close - 2,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume
    }, index=dates)

@pytest.fixture
def builder():
    settings = Settings()
    engine = IndicatorEngine(settings=settings)
    return MomentumFeatureBuilder(indicator_engine=engine, settings=settings)

def test_default_requests_basic(builder):
    reqs = builder.default_momentum_requests("basic")
    names = [r.name for r in reqs]
    assert "rsi_enhanced" in names
    assert "roc_pct" in names
    assert "cci" not in names

def test_default_requests_advanced(builder):
    reqs = builder.default_momentum_requests("advanced")
    names = [r.name for r in reqs]
    assert "cci" in names
    assert "mfi" in names
    assert "momentum_strength" in names
    assert "rsi_enhanced" not in names

def test_default_requests_full(builder):
    reqs = builder.default_momentum_requests("full")
    names = [r.name for r in reqs]
    assert "rsi_enhanced" in names
    assert "cci" in names
    assert "momentum_strength" in names

def test_invalid_level(builder):
    with pytest.raises(ValueError):
        builder.default_momentum_requests("unknown")

def test_build_basic(builder, sample_data):
    res = builder.build_basic_momentum_features(sample_data)
    assert res.failed_count == 0
    assert "rsi_14" in res.output_data.columns
    assert "roc_pct_10" in res.output_data.columns

def test_build_advanced(builder, sample_data):
    res = builder.build_advanced_momentum_features(sample_data)
    assert res.failed_count == 0
    assert "cci_20" in res.output_data.columns
    assert "momentum_strength_score" in res.output_data.columns

def test_build_full(builder, sample_data):
    res = builder.build_full_momentum_features(sample_data)
    assert res.failed_count == 0
    assert "rsi_14" in res.output_data.columns
    assert "cci_20" in res.output_data.columns
    assert "momentum_strength_score" in res.output_data.columns
