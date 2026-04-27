from datetime import datetime

import pandas as pd

from bist_signal_bot.data.models import DataVendor, MarketDataFrame, Timeframe
from bist_signal_bot.data.quality import DataQualityChecker, DataQualityIssueType


def make_mdf(df: pd.DataFrame, symbol="ASELS", timeframe=Timeframe.DAILY) -> MarketDataFrame:
    return MarketDataFrame(
        symbol=symbol,
        timeframe=timeframe,
        source=DataVendor.INTERNAL,
        data=df,
        fetched_at=datetime.utcnow()
    )

def test_clean_data_passes():
    dates = pd.date_range("2023-01-01", periods=100, tz="Europe/Istanbul")
    df = pd.DataFrame({
        "open": [10.0] * 100,
        "high": [12.0] * 100,
        "low": [9.0] * 100,
        "close": [11.0] * 100,
        "volume": [1000] * 100
    }, index=dates)
    mdf = make_mdf(df)

    checker = DataQualityChecker(min_rows=10)
    report = checker.check(mdf)

    assert report.passed is True
    assert report.score == 100.0
    assert len(report.issues) == 0

def test_empty_dataframe():
    df = pd.DataFrame()
    mdf = make_mdf(df)

    checker = DataQualityChecker()
    report = checker.check(mdf)

    assert report.passed is False
    assert report.has_critical() is True
    assert any(i.issue_type == DataQualityIssueType.EMPTY_DATA for i in report.issues)

def test_missing_columns():
    dates = pd.date_range("2023-01-01", periods=10, tz="Europe/Istanbul")
    df = pd.DataFrame({
        "open": [10.0] * 10,
        "close": [11.0] * 10,
    }, index=dates)

    mdf = make_mdf(df)
    checker = DataQualityChecker(min_rows=5)
    report = checker.check(mdf)

    assert report.passed is False
    assert report.has_critical() is True
    assert any(i.issue_type == DataQualityIssueType.MISSING_COLUMNS for i in report.issues)

def test_non_datetime_index():
    df = pd.DataFrame({
        "open": [10.0] * 10,
        "high": [12.0] * 10,
        "low": [9.0] * 10,
        "close": [11.0] * 10,
        "volume": [1000] * 10
    }) # default RangeIndex
    mdf = make_mdf(df)

    checker = DataQualityChecker(min_rows=5)
    report = checker.check(mdf)

    assert any(i.issue_type == DataQualityIssueType.NON_DATETIME_INDEX for i in report.issues)

def test_unsorted_index():
    dates = [datetime(2023,1,2), datetime(2023,1,1), datetime(2023,1,3)]
    df = pd.DataFrame({
        "open": [10.0] * 3,
        "high": [12.0] * 3,
        "low": [9.0] * 3,
        "close": [11.0] * 3,
        "volume": [1000] * 3
    }, index=pd.DatetimeIndex(dates))
    mdf = make_mdf(df)

    checker = DataQualityChecker(min_rows=1)
    report = checker.check(mdf)

    assert any(i.issue_type == DataQualityIssueType.UNSORTED_INDEX for i in report.issues)

def test_duplicate_timestamps():
    dates = [datetime(2023,1,1), datetime(2023,1,1), datetime(2023,1,2)]
    df = pd.DataFrame({
        "open": [10.0] * 3,
        "high": [12.0] * 3,
        "low": [9.0] * 3,
        "close": [11.0] * 3,
        "volume": [1000] * 3
    }, index=pd.DatetimeIndex(dates))
    mdf = make_mdf(df)

    checker = DataQualityChecker(min_rows=1)
    report = checker.check(mdf)

    assert any(i.issue_type == DataQualityIssueType.DUPLICATE_TIMESTAMPS for i in report.issues)

def test_missing_values():
    dates = pd.date_range("2023-01-01", periods=3, tz="Europe/Istanbul")
    df = pd.DataFrame({
        "open": [10.0, None, 10.0],
        "high": [12.0, 12.0, 12.0],
        "low": [9.0, 9.0, 9.0],
        "close": [11.0, 11.0, 11.0],
        "volume": [1000, 1000, 1000]
    }, index=dates)
    mdf = make_mdf(df)

    checker = DataQualityChecker(min_rows=1)
    report = checker.check(mdf)

    assert any(i.issue_type == DataQualityIssueType.MISSING_VALUES for i in report.issues)

def test_non_numeric_values():
    dates = pd.date_range("2023-01-01", periods=3, tz="Europe/Istanbul")
    df = pd.DataFrame({
        "open": ["10", "11", "12"],
        "high": [12.0, 12.0, 12.0],
        "low": [9.0, 9.0, 9.0],
        "close": [11.0, 11.0, 11.0],
        "volume": [1000, 1000, 1000]
    }, index=dates)
    mdf = make_mdf(df)

    checker = DataQualityChecker(min_rows=1)
    report = checker.check(mdf)

    assert any(i.issue_type == DataQualityIssueType.NON_NUMERIC_VALUES for i in report.issues)

def test_negative_values():
    dates = pd.date_range("2023-01-01", periods=3, tz="Europe/Istanbul")
    df = pd.DataFrame({
        "open": [10.0, -1.0, 10.0],
        "high": [12.0, 12.0, 12.0],
        "low": [9.0, 9.0, 9.0],
        "close": [11.0, 11.0, 11.0],
        "volume": [1000, -100, 1000]
    }, index=dates)
    mdf = make_mdf(df)

    checker = DataQualityChecker(min_rows=1)
    report = checker.check(mdf)

    assert any(i.issue_type == DataQualityIssueType.NEGATIVE_PRICE for i in report.issues)
    assert any(i.issue_type == DataQualityIssueType.NEGATIVE_VOLUME for i in report.issues)

def test_invalid_ohlc_relations():
    dates = pd.date_range("2023-01-01", periods=3, tz="Europe/Istanbul")
    df = pd.DataFrame({
        "open": [10.0, 10.0, 10.0],
        "high": [12.0, 8.0, 12.0], # high < low in row 2
        "low": [9.0, 9.0, 15.0],   # low > open/close in row 3
        "close": [11.0, 11.0, 11.0],
        "volume": [1000, 1000, 1000]
    }, index=dates)
    mdf = make_mdf(df)

    checker = DataQualityChecker(min_rows=1)
    report = checker.check(mdf)

    issues = [i for i in report.issues if i.issue_type == DataQualityIssueType.INVALID_OHLC_RELATION]
    assert len(issues) > 0

def test_zero_volume_series():
    dates = pd.date_range("2023-01-01", periods=3, tz="Europe/Istanbul")
    df = pd.DataFrame({
        "open": [10.0] * 3,
        "high": [12.0] * 3,
        "low": [9.0] * 3,
        "close": [11.0] * 3,
        "volume": [0] * 3
    }, index=dates)
    mdf = make_mdf(df)

    checker = DataQualityChecker(min_rows=1)
    report = checker.check(mdf)

    assert any(i.issue_type == DataQualityIssueType.ZERO_VOLUME_SERIES for i in report.issues)

def test_large_date_gaps():
    dates = [datetime(2023,1,1), datetime(2023,1,2), datetime(2023,1,20)]
    df = pd.DataFrame({
        "open": [10.0] * 3,
        "high": [12.0] * 3,
        "low": [9.0] * 3,
        "close": [11.0] * 3,
        "volume": [1000] * 3
    }, index=pd.DatetimeIndex(dates))
    mdf = make_mdf(df)

    checker = DataQualityChecker(min_rows=1, max_allowed_gap_days=10)
    report = checker.check(mdf)

    assert any(i.issue_type == DataQualityIssueType.LARGE_DATE_GAP for i in report.issues)

def test_extreme_return():
    dates = pd.date_range("2023-01-01", periods=3, tz="Europe/Istanbul")
    df = pd.DataFrame({
        "open": [10.0] * 3,
        "high": [12.0] * 3,
        "low": [9.0] * 3,
        "close": [10.0, 15.0, 10.0], # 50% up then down
        "volume": [1000] * 3
    }, index=dates)
    mdf = make_mdf(df)

    checker = DataQualityChecker(min_rows=1, max_daily_return_abs=0.35)
    report = checker.check(mdf)

    assert any(i.issue_type == DataQualityIssueType.EXTREME_RETURN for i in report.issues)

def test_insufficient_rows():
    dates = pd.date_range("2023-01-01", periods=10, tz="Europe/Istanbul")
    df = pd.DataFrame({
        "open": [10.0] * 10,
        "high": [12.0] * 10,
        "low": [9.0] * 10,
        "close": [11.0] * 10,
        "volume": [1000] * 10
    }, index=dates)
    mdf = make_mdf(df)

    checker = DataQualityChecker(min_rows=100)
    report = checker.check(mdf)

    assert any(i.issue_type == DataQualityIssueType.INSUFFICIENT_ROWS for i in report.issues)
    assert report.score < 100.0

def test_score_range():
    df = pd.DataFrame()
    mdf = make_mdf(df)
    checker = DataQualityChecker()
    report = checker.check(mdf)

    assert 0 <= report.score <= 100
    assert report.score <= 20 # Empty is critical
