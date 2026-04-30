import pytest
import pandas as pd
import numpy as np
from bist_signal_bot.indicators.native import (
    SMAIndicator, EMAIndicator, WMAIndicator, RSIIndicator, ROCIndicator,
    TrueRangeIndicator, ATRIndicator, BollingerBandsIndicator, MACDIndicator,
    StochasticIndicator, OBVIndicator, VWAPIndicator, DailyReturnIndicator,
    LogReturnIndicator, RollingVolatilityIndicator
)
from bist_signal_bot.core.exceptions import IndicatorValidationError

@pytest.fixture
def sample_data():
    dates = pd.date_range("2024-01-01", periods=100)
    # create a simple trend
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

def test_sma(sample_data):
    ind = SMAIndicator()
    res = ind(sample_data, window=10)
    assert "sma_10" in res.columns
    assert len(res) == 100
    # First 9 should be non-null in our implementation (min_periods=1)
    assert not res["sma_10"].isna().all()

def test_sma_invalid_param(sample_data):
    ind = SMAIndicator()
    with pytest.raises(IndicatorValidationError):
        ind(sample_data, window=-5)

def test_ema(sample_data):
    ind = EMAIndicator()
    res = ind(sample_data, span=20)
    assert "ema_20" in res.columns

def test_wma(sample_data):
    ind = WMAIndicator()
    res = ind(sample_data, window=20)
    assert "wma_20" in res.columns

def test_rsi(sample_data):
    ind = RSIIndicator()
    res = ind(sample_data, window=14)
    assert "rsi_14" in res.columns
    # With a straight uptrend, RSI should quickly approach 100
    assert res["rsi_14"].iloc[-1] > 90

def test_roc(sample_data):
    ind = ROCIndicator()
    res = ind(sample_data, window=10)
    assert "roc_10" in res.columns

def test_true_range(sample_data):
    ind = TrueRangeIndicator()
    res = ind(sample_data)
    assert "tr" in res.columns
    # High - Low is 10
    assert np.allclose(res["tr"].iloc[1:], 10.0)

def test_atr(sample_data):
    ind = ATRIndicator()
    res = ind(sample_data, window=14)
    assert "atr_14" in res.columns

def test_bollinger_bands(sample_data):
    ind = BollingerBandsIndicator()
    res = ind(sample_data, window=20, std=2.0)
    assert "bb_mid_20" in res.columns
    assert "bb_upper_20_2_0" in res.columns
    assert "bb_lower_20_2_0" in res.columns
    assert "bb_width_20_2_0" in res.columns

def test_macd(sample_data):
    ind = MACDIndicator()
    res = ind(sample_data, fast=12, slow=26, signal=9)
    assert "macd_12_26_9" in res.columns
    assert "macd_signal_12_26_9" in res.columns
    assert "macd_hist_12_26_9" in res.columns

def test_macd_invalid_params(sample_data):
    ind = MACDIndicator()
    with pytest.raises(IndicatorValidationError):
        ind(sample_data, fast=26, slow=12) # Fast >= Slow

def test_stochastic(sample_data):
    ind = StochasticIndicator()
    res = ind(sample_data, k_window=14, d_window=3)
    assert "stoch_k_14" in res.columns
    assert "stoch_d_14_3" in res.columns

def test_obv(sample_data):
    ind = OBVIndicator()
    res = ind(sample_data)
    assert "obv" in res.columns

def test_vwap(sample_data):
    ind = VWAPIndicator()
    res = ind(sample_data, window=20)
    assert "vwap_20" in res.columns

def test_returns(sample_data):
    ind1 = DailyReturnIndicator()
    res1 = ind1(sample_data, periods=1)
    assert "return_1" in res1.columns

    ind2 = LogReturnIndicator()
    res2 = ind2(sample_data, periods=1)
    assert "log_return_1" in res2.columns

def test_volatility(sample_data):
    ind = RollingVolatilityIndicator()
    res = ind(sample_data, window=20)
    assert "volatility_20" in res.columns

def test_missing_required_column():
    df = pd.DataFrame({"open": [1, 2], "high": [1, 2]})
    ind = SMAIndicator()
    with pytest.raises(IndicatorValidationError):
        ind(df)

def test_input_mutation(sample_data):
    ind = SMAIndicator()
    original_cols = list(sample_data.columns)
    ind(sample_data)
    assert list(sample_data.columns) == original_cols # Input should not be mutated
