import pytest
from bist_signal_bot.markets.models import (
    MarketDefinition, MarketType, ExchangeRegion, QuoteConvention, MarketStatus,
    InstrumentDefinition, AssetClass, SymbolMapping, MarketCalendarDay, MarketSessionStatus,
    MarketSession, CurrencyDefinition, MarketUniverse, MarketNormalizationResult,
    MarketValidationResult, MarketGovernanceAssessment, MarketRegistryReport
)
from datetime import datetime

def test_market_definition():
    m = MarketDefinition(
        market_id="BIST_EQUITY",
        name="Borsa Istanbul Equities",
        market_type=MarketType.EQUITY,
        region=ExchangeRegion.TURKIYE,
        default_currency="TRY",
        timezone="Europe/Istanbul",
        quote_convention=QuoteConvention.PRICE,
        status=MarketStatus.ACTIVE
    )
    assert m.market_id == "BIST_EQUITY"
    assert "No real order was sent" in m.disclaimer

def test_instrument_definition():
    i = InstrumentDefinition(
        instrument_id="BIST_ASELS",
        market_id="BIST_EQUITY",
        symbol="ASELS",
        canonical_symbol="BIST:ASELS",
        asset_class=AssetClass.EQUITY,
        currency="TRY",
        active=True
    )
    assert i.canonical_symbol == "BIST:ASELS"
    assert "No real order was sent" in i.disclaimer
