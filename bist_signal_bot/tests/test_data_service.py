import pytest
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.data.mock_provider import MockMarketDataProvider
from bist_signal_bot.data.symbol_universe import SymbolUniverse
from bist_signal_bot.data.models import SymbolInfo
from bist_signal_bot.core.exceptions import SymbolUniverseError, InvalidSymbolError
from bist_signal_bot.data.models import Timeframe

@pytest.fixture
def data_service_without_universe():
    provider = MockMarketDataProvider(rows=50)
    return MarketDataService(provider=provider)

@pytest.fixture
def data_service_with_universe():
    provider = MockMarketDataProvider(rows=50)
    universe = SymbolUniverse([SymbolInfo(symbol="ASELS"), SymbolInfo(symbol="THYAO")])
    return MarketDataService(provider=provider, universe=universe)

def test_data_service_no_universe(data_service_without_universe):
    # Should work for any valid symbol
    mdf = data_service_without_universe.get_ohlcv("GARAN", Timeframe.DAILY)
    assert not mdf.is_empty()
    assert mdf.symbol == "GARAN"

def test_data_service_with_universe_valid(data_service_with_universe):
    mdf = data_service_with_universe.get_ohlcv("ASELS", Timeframe.DAILY)
    assert not mdf.is_empty()
    assert mdf.symbol == "ASELS"

def test_data_service_with_universe_invalid(data_service_with_universe):
    with pytest.raises(SymbolUniverseError, match="not found in the configured SymbolUniverse"):
        data_service_with_universe.get_ohlcv("GARAN", Timeframe.DAILY)

def test_data_service_invalid_symbol_format(data_service_without_universe):
    with pytest.raises(InvalidSymbolError, match="is not a valid internal"):
        data_service_without_universe.get_ohlcv("INVALID-SYMBOL", Timeframe.DAILY)

def test_data_service_get_many(data_service_with_universe):
    results = data_service_with_universe.get_many_ohlcv(["ASELS", "THYAO"], Timeframe.DAILY)
    assert len(results) == 2
    assert "ASELS" in results
    assert "THYAO" in results
    assert not results["ASELS"].is_empty()
    assert not results["THYAO"].is_empty()

def test_data_service_provider_status(data_service_without_universe):
    status = data_service_without_universe.provider_status()
    assert status["name"] == "Mock Provider"
    assert status["vendor"] == "INTERNAL"
    assert status["is_available"] is True
