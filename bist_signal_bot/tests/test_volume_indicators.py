import pytest
import pandas as pd
import numpy as np

from bist_signal_bot.core.exceptions import IndicatorValidationError
from bist_signal_bot.indicators.volume import (
    VolumeSMAIndicator, VolumeEMAIndicator, VolumeRatioIndicator,
    VolumeROCIndicator, VolumeZScoreIndicator, VolumeSpikeIndicator,
    TurnoverTRYProxyIndicator, VWMAIndicator, VWMADistanceIndicator,
    VWAPEnhancedIndicator, OBVEnhancedIndicator, ADLIndicator,
    CMFIndicator, ChaikinOscillatorIndicator, PVTIndicator,
    ForceIndexIndicator, EaseOfMovementIndicator, NVIIndicator,
    PVIIndicator, KVOIndicator, VolumeBreakoutConfirmationIndicator,
    LiquidityScoreIndicator, VolumeCompositeScoreIndicator
)

@pytest.fixture
def mock_volume_data():
    dates = pd.date_range("2023-01-01", periods=100)
    data = {
        "volume": np.linspace(1000, 3900, 100),
        "close": np.linspace(10, 39, 100),
        "high": np.linspace(11, 40, 100),
        "low": np.linspace(9, 38, 100)
    }
    # add a zero volume for division safety tests
    data["volume"][5] = 0.0
    return pd.DataFrame(data, index=dates)

def test_volume_sma(mock_volume_data):
    ind = VolumeSMAIndicator()
    res = ind(mock_volume_data, window=5)
    assert "volume_sma_5" in res.columns
    assert len(res) == len(mock_volume_data)

def test_volume_ema(mock_volume_data):
    ind = VolumeEMAIndicator()
    res = ind(mock_volume_data, span=10)
    assert "volume_ema_10" in res.columns

def test_volume_ratio(mock_volume_data):
    ind = VolumeRatioIndicator()
    res = ind(mock_volume_data, window=5)
    assert "volume_ratio_5" in res.columns

def test_volume_roc(mock_volume_data):
    ind = VolumeROCIndicator()
    res = ind(mock_volume_data, window=5)
    assert "volume_roc_5" in res.columns

def test_volume_zscore(mock_volume_data):
    ind = VolumeZScoreIndicator()
    res = ind(mock_volume_data, window=5)
    assert "volume_zscore_5" in res.columns

def test_volume_spike(mock_volume_data):
    ind = VolumeSpikeIndicator()
    df = mock_volume_data.copy()
    df.loc[df.index[10], "volume"] = df["volume"].iloc[0:10].mean() * 3
    res = ind(df, window=5, multiplier=2.0)
    assert "volume_spike_5_2_0" in res.columns
    assert "volume_spike_ratio_5" in res.columns
    assert res["volume_spike_5_2_0"].iloc[10] == 1.0

def test_turnover_try(mock_volume_data):
    ind = TurnoverTRYProxyIndicator()
    res = ind(mock_volume_data, window=5)
    assert "turnover_try" in res.columns
    assert "turnover_try_sma_5" in res.columns

def test_vwma(mock_volume_data):
    ind = VWMAIndicator()
    res = ind(mock_volume_data, window=5)
    assert "vwma_5" in res.columns

def test_vwma_distance(mock_volume_data):
    ind = VWMADistanceIndicator()
    res = ind(mock_volume_data, window=5)
    assert "vwma_distance_5" in res.columns

def test_adl(mock_volume_data):
    ind = ADLIndicator()
    res = ind(mock_volume_data)
    assert "adl" in res.columns

def test_cmf(mock_volume_data):
    ind = CMFIndicator()
    res = ind(mock_volume_data, window=5)
    assert "cmf_5" in res.columns

def test_chaikin_oscillator(mock_volume_data):
    ind = ChaikinOscillatorIndicator()
    res = ind(mock_volume_data, fast=3, slow=5)
    assert "chaikin_osc_3_5" in res.columns

def test_pvt(mock_volume_data):
    ind = PVTIndicator()
    res = ind(mock_volume_data)
    assert "pvt" in res.columns

def test_force_index(mock_volume_data):
    ind = ForceIndexIndicator()
    res = ind(mock_volume_data, ema_span=5)
    assert "force_index" in res.columns
    assert "force_index_ema_5" in res.columns

def test_eom(mock_volume_data):
    ind = EaseOfMovementIndicator()
    res = ind(mock_volume_data, window=5)
    assert "eom" in res.columns
    assert "eom_sma_5" in res.columns

def test_nvi(mock_volume_data):
    ind = NVIIndicator()
    res = ind(mock_volume_data)
    assert "nvi" in res.columns

def test_pvi(mock_volume_data):
    ind = PVIIndicator()
    res = ind(mock_volume_data)
    assert "pvi" in res.columns

def test_kvo(mock_volume_data):
    ind = KVOIndicator()
    res = ind(mock_volume_data, fast=5, slow=10, signal=3)
    assert "kvo_5_10" in res.columns

def test_vwap_enhanced(mock_volume_data):
    ind = VWAPEnhancedIndicator()
    res = ind(mock_volume_data, window=5)
    assert "vwap_5" in res.columns
    assert "vwap_distance_5" in res.columns

def test_obv_enhanced(mock_volume_data):
    ind = OBVEnhancedIndicator()
    res = ind(mock_volume_data, slope_window=5)
    assert "obv" in res.columns
    assert "obv_slope_5" in res.columns
    assert "obv_direction_5" in res.columns

def test_volume_breakout(mock_volume_data):
    ind = VolumeBreakoutConfirmationIndicator()
    df = mock_volume_data.copy()
    df.loc[df.index[25], "close"] = df["high"].iloc[:25].max() * 1.5
    df.loc[df.index[25], "volume"] = df["volume"].iloc[:25].mean() * 3
    res = ind(df, volume_window=5, price_window=5)
    assert "volume_breakout_confirm_5_5" in res.columns
    assert res["volume_breakout_confirm_5_5"].iloc[25] == 1.0

def test_liquidity_score(mock_volume_data):
    ind = LiquidityScoreIndicator()
    res = ind(mock_volume_data, window=5, min_turnover_try=1000.0)
    assert "liquidity_score_5" in res.columns

def test_volume_composite(mock_volume_data):
    ind = VolumeCompositeScoreIndicator()
    res = ind(mock_volume_data, volume_window=5, price_window=5)
    assert "volume_activity_score" in res.columns
    assert "volume_pressure_score" in res.columns
