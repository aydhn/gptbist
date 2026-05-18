import pytest
import pandas as pd
from unittest.mock import MagicMock
from bist_signal_bot.data.providers_v2.fallback import FallbackProviderRouter
from bist_signal_bot.data.providers_v2.models import ProviderRequest, ProviderResponse, DataFetchStatus, ProviderType, DataLineageSource
from bist_signal_bot.config.settings import Settings

def test_fallback_router_success():
    settings = Settings()

    mock_local = MagicMock()
    mock_local.provider_type.return_value = ProviderType.LOCAL_FILE
    mock_local.fetch.return_value = ProviderResponse(
        request=ProviderRequest(symbols=["ASELS"], timeframe="1d"),
        status=DataFetchStatus.SUCCESS,
        data_by_symbol={"ASELS": pd.DataFrame({'date': [1]})},
        lineage=[DataLineageSource(source_id="1", provider_type=ProviderType.LOCAL_FILE, provider_name="local", symbol="ASELS", timeframe="1d", fetched_at=pd.Timestamp.utcnow(), row_count=1)]
    )

    mock_yf = MagicMock()
    mock_yf.provider_type.return_value = ProviderType.YFINANCE

    router = FallbackProviderRouter([mock_local, mock_yf], settings)
    req = ProviderRequest(symbols=["ASELS"], timeframe="1d", provider_order=[ProviderType.LOCAL_FILE, ProviderType.YFINANCE])
    res = router.fetch(req)

    assert res.status == DataFetchStatus.SUCCESS
    assert "ASELS" in res.data_by_symbol
    mock_local.fetch.assert_called_once()
    mock_yf.fetch.assert_not_called()

def test_fallback_router_missing_data():
    settings = Settings()

    mock_local = MagicMock()
    mock_local.provider_type.return_value = ProviderType.LOCAL_FILE
    mock_local.fetch.return_value = ProviderResponse(
        request=ProviderRequest(symbols=["ASELS"], timeframe="1d"),
        status=DataFetchStatus.EMPTY,
        data_by_symbol={},
        lineage=[]
    )

    mock_yf = MagicMock()
    mock_yf.provider_type.return_value = ProviderType.YFINANCE
    mock_yf.fetch.return_value = ProviderResponse(
        request=ProviderRequest(symbols=["ASELS"], timeframe="1d"),
        status=DataFetchStatus.SUCCESS,
        data_by_symbol={"ASELS": pd.DataFrame({'date': [1]})},
        lineage=[DataLineageSource(source_id="2", provider_type=ProviderType.YFINANCE, provider_name="yf", symbol="ASELS", timeframe="1d", fetched_at=pd.Timestamp.utcnow(), row_count=1)]
    )

    router = FallbackProviderRouter([mock_local, mock_yf], settings)
    req = ProviderRequest(symbols=["ASELS"], timeframe="1d", provider_order=[ProviderType.LOCAL_FILE, ProviderType.YFINANCE])
    res = router.fetch(req)

    assert res.status == DataFetchStatus.SUCCESS
    assert "ASELS" in res.data_by_symbol
    mock_local.fetch.assert_called_once()
    mock_yf.fetch.assert_called_once()
