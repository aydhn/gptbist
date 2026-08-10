import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from bist_signal_bot.data.providers_v2.yfinance_provider import YFinanceProviderV2
from bist_signal_bot.data.providers_v2.models import ProviderRequest, DataFetchStatus

def test_yfinance_network_not_allowed():
    provider = YFinanceProviderV2()
    req = ProviderRequest(symbols=["ASELS"], timeframe="1d", allow_network=False)
    res = provider.fetch(req)
    assert res.status == DataFetchStatus.SKIPPED

@patch('yfinance.download')
@patch('bist_signal_bot.data.providers_v2.yfinance_provider.get_settings')
def test_yfinance_success(mock_get_settings, mock_download):
    mock_settings = MagicMock()
    mock_settings.DATA_YFINANCE_SUFFIX = ".IS"
    mock_get_settings.return_value = mock_settings

    df = pd.DataFrame({'Datetime': ['2023-01-01'], 'Close': [10.0], 'Open': [10.0], 'High': [10.0], 'Low': [10.0], 'Volume': [1000]})
    mock_download.return_value = df

    provider = YFinanceProviderV2()
    req = ProviderRequest(symbols=["ASELS"], timeframe="1d", allow_network=True)
    res = provider.fetch(req)

    assert res.status == DataFetchStatus.SUCCESS
    assert "ASELS" in res.data_by_symbol

from bist_signal_bot.data.yfinance_provider import YFinanceMarketDataProvider
from bist_signal_bot.data.models import DataFetchRequest, Timeframe

@patch('yfinance.download')
def test_yfinance_provider_batch_ohlcv(mock_download):
    # Setup mock dataframe matching yfinance output for multi-index
    columns = pd.MultiIndex.from_product([['ASELS.IS', 'GARAN.IS'], ['Open', 'High', 'Low', 'Close', 'Volume']], names=['Ticker', 'Price'])
    df = pd.DataFrame([[10, 11, 9, 10.5, 1000] * 2], columns=columns, index=[pd.Timestamp('2023-01-01')])
    mock_download.return_value = df

    provider = YFinanceMarketDataProvider()
    req = DataFetchRequest(symbols=["ASELS", "GARAN"], timeframe=Timeframe.DAILY, period="1mo")
    res = provider.fetch_ohlcv(req)

    assert "ASELS" in res
    assert "GARAN" in res
    assert not res["ASELS"].data.empty
    assert res["ASELS"].data.iloc[0]["open"] == 10
