import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from bist_signal_bot.data.providers_v2.local_file import LocalFileProvider
from bist_signal_bot.data.providers_v2.models import ProviderRequest, DataFetchStatus

def test_local_provider_empty():
    provider = LocalFileProvider()
    req = ProviderRequest(symbols=["MISSING"], timeframe="1d")

    with patch.object(provider, 'load_symbol_data', return_value=None):
        res = provider.fetch(req)

    assert res.status == DataFetchStatus.EMPTY
    assert "No local data found" in res.warnings[0]

def test_local_provider_success():
    provider = LocalFileProvider()
    req = ProviderRequest(symbols=["ASELS"], timeframe="1d")
    df = pd.DataFrame({'date': ['2023-01-01'], 'close': [10.0]})

    with patch.object(provider, 'load_symbol_data', return_value=df):
        res = provider.fetch(req)

    assert res.status == DataFetchStatus.SUCCESS
    assert "ASELS" in res.data_by_symbol
    assert len(res.lineage) == 1
