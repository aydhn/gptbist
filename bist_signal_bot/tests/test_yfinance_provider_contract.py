from bist_signal_bot.data.models import DataVendor
from bist_signal_bot.data.yfinance_provider import YFinanceMarketDataProvider


def test_yfinance_provider_attributes():
    provider = YFinanceMarketDataProvider()
    assert provider.name == "YFinance Provider"
    assert provider.vendor == DataVendor.YFINANCE
    assert provider.supports_intraday is True
    assert provider.supports_adjusted is True

def test_yfinance_provider_normalize_symbol():
    provider = YFinanceMarketDataProvider()
    assert provider.normalize_provider_symbol("ASELS") == "ASELS.IS"
    assert provider.normalize_provider_symbol("GARAN.IS") == "GARAN.IS"

def test_yfinance_provider_is_available():
    provider = YFinanceMarketDataProvider()
    # It should return a boolean based on whether yfinance is installed
    assert isinstance(provider.is_available(), bool)
