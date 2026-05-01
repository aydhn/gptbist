import pytest
import pandas as pd
import numpy as np
from bist_signal_bot.indicators.volatility import (
    ATRPercentIndicator, NormalizedTrueRangeIndicator, HistoricalVolatilityIndicator,
    RealizedVolatilityIndicator, ParkinsonVolatilityIndicator, GarmanKlassVolatilityIndicator,
    RogersSatchellVolatilityIndicator, RangePercentIndicator, GapPercentIndicator,
    BollingerBandwidthPercentileIndicator, ATRPercentileIndicator, VolatilityZScoreIndicator,
    VolatilityCompressionScoreIndicator, VolatilityExpansionScoreIndicator,
    VolatilityRegimeFeatureIndicator, VolatilityCompositeScoreIndicator
)
from bist_signal_bot.core.exceptions import IndicatorValidationError

@pytest.fixture
def sample_data():
    dates = pd.date_range("2024-01-01", periods=300)
    close = np.linspace(100, 200, 300)
    high = close + 5
    low = close - 5
    return pd.DataFrame({
        "open": close - 2,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.random.randint(1000, 5000, 300)
    }, index=dates)

def test_atr_pct(sample_data):
    ind = ATRPercentIndicator()
    res = ind(sample_data, window=14)
    assert "atr_pct_14" in res.columns
    assert not res["atr_pct_14"].dropna().empty
    assert (res["atr_pct_14"].dropna() >= 0).all()

def test_ntr(sample_data):
    ind = NormalizedTrueRangeIndicator()
    res = ind(sample_data, window=14)
    assert "ntr_14" in res.columns
    assert "ntr_ma_14" in res.columns
    assert not res["ntr_14"].dropna().empty

def test_historical_vol(sample_data):
    ind = HistoricalVolatilityIndicator()
    res = ind(sample_data, window=20, annualization=252)
    assert "hist_vol_20" in res.columns
    assert not res["hist_vol_20"].dropna().empty

def test_realized_vol(sample_data):
    ind = RealizedVolatilityIndicator()
    res = ind(sample_data, window=20)
    assert "realized_vol_20" in res.columns
    assert not res["realized_vol_20"].dropna().empty

def test_parkinson_vol(sample_data):
    ind = ParkinsonVolatilityIndicator()
    res = ind(sample_data, window=20)
    assert "parkinson_vol_20" in res.columns
    assert not res["parkinson_vol_20"].dropna().empty

def test_garman_klass_vol(sample_data):
    ind = GarmanKlassVolatilityIndicator()
    res = ind(sample_data, window=20)
    assert "garman_klass_vol_20" in res.columns
    assert not res["garman_klass_vol_20"].dropna().empty

def test_rogers_satchell_vol(sample_data):
    ind = RogersSatchellVolatilityIndicator()
    res = ind(sample_data, window=20)
    assert "rogers_satchell_vol_20" in res.columns
    assert not res["rogers_satchell_vol_20"].dropna().empty

def test_range_pct(sample_data):
    ind = RangePercentIndicator()
    res = ind(sample_data, window=20)
    assert "range_pct" in res.columns
    assert "range_pct_zscore_20" in res.columns

def test_gap_pct(sample_data):
    ind = GapPercentIndicator()
    res = ind(sample_data, window=20)
    assert "gap_pct" in res.columns
    assert "gap_pct_zscore_20" in res.columns

def test_bb_width_percentile(sample_data):
    ind = BollingerBandwidthPercentileIndicator()
    res = ind(sample_data, window=20, std=2.0, rank_window=100)
    assert "bb_width_percentile_20_100" in res.columns
    valid = res["bb_width_percentile_20_100"].dropna()
    if not valid.empty:
        assert valid.min() >= 0
        assert valid.max() <= 100

def test_atr_percentile(sample_data):
    ind = ATRPercentileIndicator()
    res = ind(sample_data, atr_window=14, rank_window=100)
    assert "atr_pct_percentile_14_100" in res.columns
    valid = res["atr_pct_percentile_14_100"].dropna()
    if not valid.empty:
        assert valid.min() >= 0
        assert valid.max() <= 100

def test_vol_zscore(sample_data):
    ind = VolatilityZScoreIndicator()
    res = ind(sample_data, vol_window=20, z_window=100)
    assert "vol_zscore_20_100" in res.columns

def test_compression_score(sample_data):
    ind = VolatilityCompressionScoreIndicator()
    res = ind(sample_data, bb_window=20, atr_window=14, rank_window=100)
    assert "vol_compression_score" in res.columns
    valid = res["vol_compression_score"].dropna()
    if not valid.empty:
        assert valid.min() >= 0
        assert valid.max() <= 100

def test_expansion_score(sample_data):
    ind = VolatilityExpansionScoreIndicator()
    res = ind(sample_data, bb_window=20, atr_window=14, rank_window=100)
    assert "vol_expansion_score" in res.columns
    valid = res["vol_expansion_score"].dropna()
    if not valid.empty:
        assert valid.min() >= 0
        assert valid.max() <= 100

def test_regime_feature(sample_data):
    ind = VolatilityRegimeFeatureIndicator()
    res = ind(sample_data, vol_window=20, rank_window=252)
    assert "vol_regime_percentile_20_252" in res.columns
    assert "vol_regime_state_20_252" in res.columns
    valid = res["vol_regime_state_20_252"].dropna()
    if not valid.empty:
        assert set(valid.unique()).issubset({0, 1, 2})

def test_composite_score(sample_data):
    ind = VolatilityCompositeScoreIndicator()
    res = ind(sample_data, vol_window=20, atr_window=14, rank_window=100)
    assert "volatility_risk_score" in res.columns
    assert "volatility_regime_score" in res.columns
    valid_risk = res["volatility_risk_score"].dropna()
    if not valid_risk.empty:
        assert valid_risk.min() >= 0
        assert valid_risk.max() <= 100

def test_negative_window(sample_data):
    ind = ATRPercentIndicator()
    with pytest.raises(IndicatorValidationError):
        ind(sample_data, window=-5)

def test_missing_col(sample_data):
    ind = ATRPercentIndicator()
    bad_data = sample_data.drop(columns=["high"])
    with pytest.raises(IndicatorValidationError):
        ind(bad_data, window=14)

def test_no_mutate(sample_data):
    ind = ATRPercentIndicator()
    original_cols = list(sample_data.columns)
    ind(sample_data, window=14)
    assert list(sample_data.columns) == original_cols

def test_safe_log_negative_prices(sample_data):
    bad_data = sample_data.copy()
    bad_data.loc[bad_data.index[50], 'close'] = -10
    ind = HistoricalVolatilityIndicator()
    res = ind(bad_data, window=20)
    assert "hist_vol_20" in res.columns
    # Should not crash, just produce NaN for that specific log return
