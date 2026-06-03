from pathlib import Path
from typing import Optional
from bist_signal_bot.markets.storage import MarketStore
from bist_signal_bot.markets.registry import MarketRegistry
from bist_signal_bot.markets.instruments import InstrumentRegistry
from bist_signal_bot.markets.symbols import SymbolNormalizer
from bist_signal_bot.markets.calendar import MarketCalendarProvider
from bist_signal_bot.markets.sessions import MarketSessionProvider
from bist_signal_bot.markets.currencies import CurrencyRegistry
from bist_signal_bot.markets.asset_classes import AssetClassRegistry
from bist_signal_bot.markets.normalization import MarketDataNormalizer
from bist_signal_bot.markets.validation import MarketValidationEngine
from bist_signal_bot.markets.universe import MarketUniverseBuilder
from bist_signal_bot.markets.governance import MarketGovernanceEngine

def create_market_store(settings=None, base_dir: Optional[Path] = None) -> MarketStore:
    d = base_dir or Path("data/markets")
    return MarketStore(d)

def create_market_registry(settings=None, base_dir: Optional[Path] = None) -> MarketRegistry:
    return MarketRegistry(create_market_store(settings, base_dir))

def create_instrument_registry(settings=None, base_dir: Optional[Path] = None) -> InstrumentRegistry:
    return InstrumentRegistry(create_market_store(settings, base_dir))

def create_symbol_normalizer(settings=None, base_dir: Optional[Path] = None) -> SymbolNormalizer:
    return SymbolNormalizer(create_market_store(settings, base_dir))

def create_market_calendar_provider(settings=None, base_dir: Optional[Path] = None) -> MarketCalendarProvider:
    return MarketCalendarProvider(create_market_store(settings, base_dir))

def create_market_session_provider(settings=None, base_dir: Optional[Path] = None) -> MarketSessionProvider:
    cal = create_market_calendar_provider(settings, base_dir)
    return MarketSessionProvider(cal, create_market_store(settings, base_dir))

def create_currency_registry(settings=None, base_dir: Optional[Path] = None) -> CurrencyRegistry:
    return CurrencyRegistry(create_market_store(settings, base_dir))

def create_asset_class_registry(settings=None, base_dir: Optional[Path] = None) -> AssetClassRegistry:
    return AssetClassRegistry(create_market_store(settings, base_dir))

def create_market_data_normalizer(settings=None, base_dir: Optional[Path] = None) -> MarketDataNormalizer:
    return MarketDataNormalizer(
        create_symbol_normalizer(settings, base_dir),
        create_market_registry(settings, base_dir)
    )

def create_market_validation_engine(settings=None, base_dir: Optional[Path] = None) -> MarketValidationEngine:
    return MarketValidationEngine(
        create_symbol_normalizer(settings, base_dir),
        create_currency_registry(settings, base_dir),
        create_instrument_registry(settings, base_dir)
    )

def create_market_universe_builder(settings=None, base_dir: Optional[Path] = None) -> MarketUniverseBuilder:
    return MarketUniverseBuilder(
        create_instrument_registry(settings, base_dir),
        create_symbol_normalizer(settings, base_dir),
        create_market_store(settings, base_dir)
    )

def create_market_governance_engine(settings=None, base_dir: Optional[Path] = None) -> MarketGovernanceEngine:
    return MarketGovernanceEngine(
        create_market_registry(settings, base_dir),
        create_instrument_registry(settings, base_dir),
        create_market_calendar_provider(settings, base_dir),
        create_market_store(settings, base_dir)
    )
