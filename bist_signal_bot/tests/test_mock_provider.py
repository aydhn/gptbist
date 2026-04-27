import pandas as pd

from bist_signal_bot.data.mock_provider import MockMarketDataProvider
from bist_signal_bot.data.models import Timeframe


def test_mock_provider_deterministic():
    provider = MockMarketDataProvider(seed=123, rows=100)

    mdf1 = provider.fetch_one("ASELS", timeframe=Timeframe.DAILY)
    mdf2 = provider.fetch_one("ASELS", timeframe=Timeframe.DAILY)

    # Check shape
    assert mdf1.row_count() == mdf2.row_count()

    # Check determinism
    pd.testing.assert_frame_equal(mdf1.data, mdf2.data)

def test_mock_provider_symbol_differs():
    provider = MockMarketDataProvider(seed=123, rows=100)

    mdf1 = provider.fetch_one("ASELS", timeframe=Timeframe.DAILY)
    mdf2 = provider.fetch_one("THYAO", timeframe=Timeframe.DAILY)

    assert not mdf1.data.equals(mdf2.data)

def test_mock_provider_ohlc_rules():
    provider = MockMarketDataProvider(rows=100)
    mdf = provider.fetch_one("GARAN", timeframe=Timeframe.DAILY)
    df = mdf.data

    assert (df["high"] >= df["low"]).all()
    assert (df["high"] >= df["open"]).all()
    assert (df["high"] >= df["close"]).all()
    assert (df["low"] <= df["open"]).all()
    assert (df["low"] <= df["close"]).all()
    assert (df["volume"] > 0).all()
    assert (df >= 0).all().all() # all prices positive
