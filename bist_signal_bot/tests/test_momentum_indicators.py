import pytest
import pandas as pd
import numpy as np

from bist_signal_bot.core.exceptions import IndicatorValidationError
from bist_signal_bot.indicators.momentum import (
    MomentumIndicator, RateOfChangePercentIndicator, RSIEnhancedIndicator,
    StochasticEnhancedIndicator, WilliamsRIndicator, CCIIndicator, MFIIndicator,
    TSIIndicator, UltimateOscillatorIndicator, PPOIndicator, KSTIndicator,
    ConnorsRSIIndicator, MomentumStrengthCompositeIndicator
)

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

def test_momentum_indicator(sample_data):
    ind = MomentumIndicator()
    res = ind(sample_data, window=10)
    assert "momentum_10" in res.columns
    # 200 - 190 (since linspace)
    assert not res["momentum_10"].isna().all()

def test_roc_pct_indicator(sample_data):
    ind = RateOfChangePercentIndicator()
    res = ind(sample_data, window=10)
    assert "roc_pct_10" in res.columns
    assert not res["roc_pct_10"].isna().all()

def test_rsi_enhanced(sample_data):
    ind = RSIEnhancedIndicator()
    res = ind(sample_data, window=14, slope_window=3)
    assert "rsi_14" in res.columns
    assert "rsi_slope_14_3" in res.columns
    assert "rsi_zone_14" in res.columns
    assert "rsi_above_50_14" in res.columns

    assert res["rsi_zone_14"].isin([-1.0, 0.0, 1.0, np.nan]).all()

def test_rsi_enhanced_invalid(sample_data):
    ind = RSIEnhancedIndicator()
    with pytest.raises(IndicatorValidationError):
        ind(sample_data, overbought=30, oversold=70) # wrong way

def test_stoch_enhanced(sample_data):
    ind = StochasticEnhancedIndicator()
    res = ind(sample_data, k_window=14, d_window=3)
    assert "stoch_k_14" in res.columns
    assert "stoch_d_14_3" in res.columns
    assert "stoch_state_14_3" in res.columns
    assert "stoch_cross_event_14_3" in res.columns
    assert res["stoch_cross_event_14_3"].isin([-1.0, 0.0, 1.0, np.nan]).all()

def test_williams_r(sample_data):
    ind = WilliamsRIndicator()
    res = ind(sample_data, window=14)
    assert "williams_r_14" in res.columns
    valid_mask = res["williams_r_14"].notna()
    assert (res.loc[valid_mask, "williams_r_14"] <= 0).all()
    assert (res.loc[valid_mask, "williams_r_14"] >= -100).all()

def test_cci(sample_data):
    ind = CCIIndicator()
    res = ind(sample_data, window=20)
    assert "cci_20" in res.columns
    assert not res["cci_20"].isna().all()

def test_mfi(sample_data):
    ind = MFIIndicator()
    res = ind(sample_data, window=14)
    assert "mfi_14" in res.columns
    valid_mask = res["mfi_14"].notna()
    assert (res.loc[valid_mask, "mfi_14"] >= 0).all()
    assert (res.loc[valid_mask, "mfi_14"] <= 100).all()

def test_tsi(sample_data):
    ind = TSIIndicator()
    res = ind(sample_data, slow=25, fast=13, signal=7)
    assert "tsi_25_13" in res.columns
    assert "tsi_signal_25_13_7" in res.columns
    assert "tsi_hist_25_13_7" in res.columns

def test_tsi_invalid(sample_data):
    ind = TSIIndicator()
    with pytest.raises(IndicatorValidationError):
        ind(sample_data, slow=13, fast=25)

def test_ultimate_oscillator(sample_data):
    ind = UltimateOscillatorIndicator()
    res = ind(sample_data, short_window=7, medium_window=14, long_window=28)
    assert "ultimate_osc_7_14_28" in res.columns
    valid_mask = res["ultimate_osc_7_14_28"].notna()
    assert (res.loc[valid_mask, "ultimate_osc_7_14_28"] >= 0).all()
    assert (res.loc[valid_mask, "ultimate_osc_7_14_28"] <= 100).all()

def test_ultimate_oscillator_invalid(sample_data):
    ind = UltimateOscillatorIndicator()
    with pytest.raises(IndicatorValidationError):
        ind(sample_data, short_window=28, medium_window=14, long_window=7)

def test_ppo(sample_data):
    ind = PPOIndicator()
    res = ind(sample_data, fast=12, slow=26, signal=9)
    assert "ppo_12_26_9" in res.columns
    assert "ppo_signal_12_26_9" in res.columns
    assert "ppo_hist_12_26_9" in res.columns

def test_ppo_invalid(sample_data):
    ind = PPOIndicator()
    with pytest.raises(IndicatorValidationError):
        ind(sample_data, fast=26, slow=12)

def test_kst(sample_data):
    ind = KSTIndicator()
    res = ind(sample_data, signal=9)
    assert "kst" in res.columns
    assert "kst_signal_9" in res.columns
    assert "kst_hist_9" in res.columns

def test_connors_rsi(sample_data):
    ind = ConnorsRSIIndicator()
    res = ind(sample_data, rsi_window=3, streak_rsi_window=2, rank_window=100)
    assert "connors_rsi_3_2_100" in res.columns

def test_momentum_strength(sample_data):
    ind = MomentumStrengthCompositeIndicator()
    res = ind(sample_data)
    assert "momentum_strength_score" in res.columns
    assert "momentum_direction_score" in res.columns

    valid_mask = res["momentum_strength_score"].notna()
    assert (res.loc[valid_mask, "momentum_strength_score"] >= 0).all()
    assert (res.loc[valid_mask, "momentum_strength_score"] <= 100).all()

    assert (res.loc[valid_mask, "momentum_direction_score"] >= -100).all()
    assert (res.loc[valid_mask, "momentum_direction_score"] <= 100).all()

def test_missing_required_col(sample_data):
    ind = MomentumIndicator()
    df = sample_data.drop(columns=["close"])
    with pytest.raises(IndicatorValidationError):
        ind(df)

def test_negative_window(sample_data):
    ind = MomentumIndicator()
    with pytest.raises(IndicatorValidationError):
        ind(sample_data, window=-5)

def test_no_mutate(sample_data):
    ind = MomentumIndicator()
    original_cols = list(sample_data.columns)
    ind(sample_data)
    assert list(sample_data.columns) == original_cols
