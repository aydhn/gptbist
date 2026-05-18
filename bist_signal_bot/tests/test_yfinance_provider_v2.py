import pytest
import pandas as pd
from unittest.mock import patch
from bist_signal_bot.data.providers_v2.yfinance_provider import YFinanceProviderV2
from bist_signal_bot.data.providers_v2.models import ProviderRequest, DataFetchStatus

def test_yfinance_network_not_allowed():
    provider = YFinanceProviderV2()
    req = ProviderRequest(symbols=["ASELS"], timeframe="1d", allow_network=False)
    res = provider.fetch(req)
    assert res.status == DataFetchStatus.SKIPPED

@patch('yfinance.download')
def test_yfinance_success(mock_download):
    df = pd.DataFrame({'Datetime': ['2023-01-01'], 'Close': [10.0]})
    mock_download.return_value = df

    provider = YFinanceProviderV2()
    req = ProviderRequest(symbols=["ASELS"], timeframe="1d", allow_network=True)
    res = provider.fetch(req)

    assert res.status == DataFetchStatus.SUCCESS
    assert "ASELS" in res.data_by_symbol
