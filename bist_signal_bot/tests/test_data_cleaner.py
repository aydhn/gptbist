import numpy as np
import pandas as pd
import pytest
from datetime import datetime, UTC, timedelta

from bist_signal_bot.data.cleaning import MarketDataCleaner
from bist_signal_bot.data.models import (
    MarketDataFrame, Timeframe, DataVendor,
    MissingValuePolicy, DuplicateTimestampPolicy, InvalidOhlcPolicy
)
from bist_signal_bot.core.exceptions import DataCleaningError
from bist_signal_bot.config.settings import Settings

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

def test_clean_success():
    cleaner = MarketDataCleaner(min_rows_after_cleaning=2)
    mdf = _make_mdf(_make_basic_df())
    res = cleaner.clean_market_data(mdf)

    assert res.report.status.value == "SUCCESS"
    assert res.report.input_rows == 5
    assert res.report.output_rows == 5
    assert res.report.usable_for_backtest is True
    assert res.market_data.metadata.get("cleaned") is True

def test_clean_mutate_not_original():
    df = _make_basic_df()
    # Add a row to drop
    df.loc[df.index[-1] + timedelta(days=1)] = [-1, 10, 5, 8, 1000]

    cleaner = MarketDataCleaner(min_rows_after_cleaning=2)
    mdf = _make_mdf(df)
    res = cleaner.clean_market_data(mdf)

    # Original should be 6 rows
    assert len(mdf.data) == 6
    # Cleaned should be 5
    assert len(res.market_data.data) == 5

def test_duplicate_timestamp_keep_last():
    df = _make_basic_df()
    df = pd.concat([df, pd.DataFrame([[12.0, 12.0, 12.0, 12.0, 2000]], index=[df.index[-1]], columns=df.columns)])

    cleaner = MarketDataCleaner(duplicate_timestamp_policy=DuplicateTimestampPolicy.KEEP_LAST)
    res = cleaner.clean_market_data(_make_mdf(df))

    assert res.report.dropped_rows == 1
    assert res.market_data.data.iloc[-1]["close"] == 12.0

def test_duplicate_timestamp_keep_first():
    df = _make_basic_df()
    df = pd.concat([df, pd.DataFrame([[12.0, 12.0, 12.0, 12.0, 2000]], index=[df.index[-1]], columns=df.columns)])

    cleaner = MarketDataCleaner(duplicate_timestamp_policy=DuplicateTimestampPolicy.KEEP_FIRST)
    res = cleaner.clean_market_data(_make_mdf(df))

    assert res.report.dropped_rows == 1
    assert res.market_data.data.iloc[-1]["close"] == 11.3

def test_duplicate_timestamp_fail():
    df = _make_basic_df()
    df = pd.concat([df, pd.DataFrame([[12.0, 12.0, 12.0, 12.0, 2000]], index=[df.index[-1]], columns=df.columns)])

    cleaner = MarketDataCleaner(duplicate_timestamp_policy=DuplicateTimestampPolicy.FAIL)
    with pytest.raises(DataCleaningError):
        cleaner.clean_market_data(_make_mdf(df))

def test_drop_empty_rows():
    df = _make_basic_df()
    df.loc[df.index[-1] + timedelta(days=1)] = [np.nan] * 5

    cleaner = MarketDataCleaner()
    res = cleaner.clean_market_data(_make_mdf(df))

    assert res.report.dropped_rows == 1
    assert len(res.market_data.data) == 5

def test_drop_negative_close():
    df = _make_basic_df()
    df.loc[df.index[2], "close"] = -5.0

    cleaner = MarketDataCleaner()
    res = cleaner.clean_market_data(_make_mdf(df))

    assert res.report.dropped_rows == 1

def test_drop_negative_volume():
    df = _make_basic_df()
    df.loc[df.index[2], "volume"] = -100

    cleaner = MarketDataCleaner()
    res = cleaner.clean_market_data(_make_mdf(df))

    assert res.report.dropped_rows == 1

def test_drop_zero_close():
    df = _make_basic_df()
    df.loc[df.index[2], "close"] = 0.0

    cleaner = MarketDataCleaner()
    res = cleaner.clean_market_data(_make_mdf(df))

    assert res.report.dropped_rows == 1

def test_usable_for_backtest_false_if_small():
    df = _make_basic_df()
    cleaner = MarketDataCleaner(min_rows_after_cleaning=10)
    res = cleaner.clean_market_data(_make_mdf(df))

    assert res.report.usable_for_backtest is False

def test_metadata_contains_cleaned():
    df = _make_basic_df()
    cleaner = MarketDataCleaner(min_rows_after_cleaning=2)
    res = cleaner.clean_market_data(_make_mdf(df))

    assert res.market_data.metadata.get("cleaned") is True
    assert res.market_data.metadata.get("cleaning_status") == "SUCCESS"
