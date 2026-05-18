import pytest
from unittest.mock import patch, MagicMock
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.data.mock_provider import MockMarketDataProvider
from bist_signal_bot.data.providers_v2.models import ProviderRequest, ImportRequest
from bist_signal_bot.config.settings import Settings

@patch('bist_signal_bot.storage.market_store.MarketStore')
def test_data_service_fetch_v2(mock_store_class):
    mock_store = MagicMock()
    mock_store_class.return_value = mock_store

    settings = Settings(DATA_YFINANCE_ENABLED=False)
    ds = MarketDataService(provider=MockMarketDataProvider())
    ds.settings = settings

    req = ProviderRequest(symbols=["ASELS"], timeframe="1d")

    res = ds.fetch_v2(req)
    assert res.status.value in ["EMPTY", "SUCCESS", "PARTIAL_SUCCESS", "SKIPPED"]

@patch('bist_signal_bot.data.importers.csv_importer.CSVMarketDataImporter')
@patch('bist_signal_bot.storage.market_store.MarketStore')
def test_data_service_import(mock_store_class, mock_importer_class):
    mock_store = MagicMock()
    mock_store_class.return_value = mock_store
    mock_importer = MagicMock()
    mock_importer_class.return_value = mock_importer

    from bist_signal_bot.data.providers_v2.models import ImportResult, DataImportStatus
    req = ImportRequest(input_path="test.csv", timeframe="1d", format="csv", symbol="ASELS")

    res_mock = ImportResult(request=req, status=DataImportStatus.IMPORTED, symbol="ASELS", timeframe="1d")
    mock_importer.import_file.return_value = res_mock

    ds = MarketDataService(provider=MockMarketDataProvider())
    ds.settings = Settings()
    res = ds.import_market_data(req)
    assert res.status == DataImportStatus.IMPORTED
