import numpy as np
import pandas as pd
import pytest
from datetime import datetime, UTC, timedelta

from bist_signal_bot.data.cleaning import MarketDataCleaner
from bist_signal_bot.data.models import CleaningConfig
from bist_signal_bot.data.models import (
    MarketDataFrame, Timeframe, DataVendor,
    MissingValuePolicy, InvalidOhlcPolicy, OutlierPolicy
)
from bist_signal_bot.core.exceptions import DataCleaningError

def _make_mdf(df: pd.DataFrame) -> MarketDataFrame:
    return MarketDataFrame(
        symbol="ASELS",
        timeframe=Timeframe.DAILY,
        source=DataVendor.INTERNAL,
        data=df,
        fetched_at=datetime.now(UTC)
    )

def _make_basic_df():
    dates = pd.date_range("2023-01-01", periods=5, tz="UTC")
    return pd.DataFrame({
        "open": [10.0, 10.5, 11.0, 10.8, 11.2],
        "high": [10.5, 11.0, 11.5, 11.2, 11.5],
        "low": [9.5, 10.0, 10.5, 10.0, 11.0],
        "close": [10.2, 10.8, 11.2, 10.5, 11.3],
        "volume": [1000, 1200, 1100, 1300, 1500]
    }, index=dates)

# INVALID OHLC
def test_invalid_ohlc_high_less_than_low():
    df = _make_basic_df()
    df.loc[df.index[2], "high"] = 9.0
    df.loc[df.index[2], "low"] = 10.0

    cleaner = MarketDataCleaner(config=CleaningConfig(invalid_ohlc_policy=InvalidOhlcPolicy.DROP_ROW))
    res = cleaner.clean_market_data(_make_mdf(df))
    assert res.report.dropped_rows == 1

def test_invalid_ohlc_high_less_than_close():
    df = _make_basic_df()
    df.loc[df.index[2], "high"] = 10.0
    df.loc[df.index[2], "close"] = 11.0

    cleaner = MarketDataCleaner()
    res = cleaner.clean_market_data(_make_mdf(df))
    assert res.report.dropped_rows == 1

def test_invalid_ohlc_low_greater_than_open():
    df = _make_basic_df()
    df.loc[df.index[2], "low"] = 12.0
    df.loc[df.index[2], "open"] = 10.0

    cleaner = MarketDataCleaner()
    res = cleaner.clean_market_data(_make_mdf(df))
    assert res.report.dropped_rows == 1

# MISSING VALUES
def test_missing_forward_fill():
    df = _make_basic_df()
    df.loc[df.index[2], "close"] = np.nan

    cleaner = MarketDataCleaner(config=CleaningConfig(missing_value_policy=MissingValuePolicy.FORWARD_FILL))
    res = cleaner.clean_market_data(_make_mdf(df))

    assert res.report.filled_values == 1
    assert res.report.dropped_rows == 0
    assert res.market_data.data.iloc[2]["close"] == 10.8 # Previous value

def test_missing_backward_fill():
    df = _make_basic_df()
    df.loc[df.index[2], "close"] = np.nan

    cleaner = MarketDataCleaner(config=CleaningConfig(missing_value_policy=MissingValuePolicy.BACKWARD_FILL))
    res = cleaner.clean_market_data(_make_mdf(df))

    assert res.report.filled_values == 1
    assert res.report.dropped_rows == 0
    assert res.market_data.data.iloc[2]["close"] == 10.5 # Next value

def test_missing_drop_row():
    df = _make_basic_df()
    df.loc[df.index[2], "close"] = np.nan

    cleaner = MarketDataCleaner(config=CleaningConfig(missing_value_policy=MissingValuePolicy.DROP_ROW))
    res = cleaner.clean_market_data(_make_mdf(df))

    assert res.report.dropped_rows == 1

def test_missing_leave_unchanged():
    df = _make_basic_df()
    df.loc[df.index[2], "close"] = np.nan

    cleaner = MarketDataCleaner(config=CleaningConfig(missing_value_policy=MissingValuePolicy.LEAVE_UNCHANGED, min_rows_after_cleaning=2))
    res = cleaner.clean_market_data(_make_mdf(df))

    assert res.report.dropped_rows == 0
    assert res.report.usable_for_ml is False # Contains NaNs
    assert res.report.status.value == "WARNING"

def test_missing_fail():
    df = _make_basic_df()
    df.loc[df.index[2], "close"] = np.nan

    cleaner = MarketDataCleaner(config=CleaningConfig(missing_value_policy=MissingValuePolicy.FAIL))
    with pytest.raises(DataCleaningError):
        cleaner.clean_market_data(_make_mdf(df))

# EXTREMES
def test_extreme_return_flag_only():
    df = _make_basic_df()
    # Create extreme return
    df.loc[df.index[2], ["high", "close"]] = [15.5, 15.0] # huge jump from 10.8

    cleaner = MarketDataCleaner(config=CleaningConfig(outlier_policy=OutlierPolicy.FLAG_ONLY, max_daily_return_abs=0.30))
    res = cleaner.clean_market_data(_make_mdf(df))

    assert res.report.dropped_rows == 0
    assert res.report.flagged_outliers > 0

def test_extreme_volume_flag_only():
    df = _make_basic_df()
    df.loc[df.index[2], "volume"] = 100000000

    cleaner = MarketDataCleaner(config=CleaningConfig(outlier_policy=OutlierPolicy.FLAG_ONLY, max_volume_zscore=1.0)) # low threshold for test
    res = cleaner.clean_market_data(_make_mdf(df))

    assert res.report.dropped_rows == 0
    assert res.report.flagged_outliers > 0
