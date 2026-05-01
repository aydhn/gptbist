import pytest
import pandas as pd
import numpy as np

from bist_signal_bot.features.volatility_features import VolatilityFeatureBuilder
from bist_signal_bot.indicators.engine import IndicatorEngine
from bist_signal_bot.config.settings import Settings

@pytest.fixture
def sample_data():
    dates = pd.date_range("2024-01-01", periods=300)
    close = np.linspace(100, 200, 300)
    high = close + 5
    low = close - 5
    volume = np.random.randint(1000, 5000, 300)
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
    return VolatilityFeatureBuilder(indicator_engine=engine, settings=settings)

def test_default_requests_basic(builder):
    reqs = builder.default_volatility_requests("basic")
    names = [r.name for r in reqs]
    assert "atr_pct" in names
    assert "historical_volatility" in names
    assert "bb_width_percentile" in names
    assert "realized_volatility" not in names

def test_default_requests_advanced(builder):
    reqs = builder.default_volatility_requests("advanced")
    names = [r.name for r in reqs]
    assert "realized_volatility" in names
    assert "garman_klass_volatility" in names
    assert "volatility_zscore" in names
    assert "atr_pct" not in names

def test_default_requests_full(builder):
    reqs = builder.default_volatility_requests("full")
    names = [r.name for r in reqs]
    assert "atr_pct" in names
    assert "realized_volatility" in names
    assert "volatility_regime" in names

def test_invalid_level(builder):
    with pytest.raises(ValueError):
        builder.default_volatility_requests("unknown")

def test_build_basic(builder, sample_data):
    res = builder.build_basic_volatility_features(sample_data)
    assert res.failed_count == 0
    assert "atr_pct_14" in res.output_data.columns
    assert "hist_vol_20" in res.output_data.columns

def test_build_advanced(builder, sample_data):
    res = builder.build_advanced_volatility_features(sample_data)
    assert res.failed_count == 0
    assert "realized_vol_20" in res.output_data.columns
    assert "vol_zscore_20_100" in res.output_data.columns

def test_build_full(builder, sample_data):
    res = builder.build_full_volatility_features(sample_data)
    assert res.failed_count == 0
    assert "atr_pct_14" in res.output_data.columns
    assert "realized_vol_20" in res.output_data.columns
    assert "vol_regime_state_20_252" in res.output_data.columns
