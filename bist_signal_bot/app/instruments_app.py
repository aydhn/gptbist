from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.instruments.master import InstrumentMaster
from bist_signal_bot.instruments.lifecycle import SymbolLifecycleManager
from bist_signal_bot.instruments.universe import InstrumentUniverseBuilder
from bist_signal_bot.instruments.importer import InstrumentImporter
from bist_signal_bot.corporate_actions.importer import CorporateActionImporter
from bist_signal_bot.corporate_actions.adjustments import PriceAdjustmentEngine
from bist_signal_bot.data.adjusted_prices import AdjustedPriceService
from bist_signal_bot.data.data_quality import DataReconciliationEngine

def create_instrument_master(settings: Settings | None = None, base_dir: Path | None = None) -> InstrumentMaster:
    return InstrumentMaster()

def create_symbol_lifecycle_manager(settings: Settings | None = None, base_dir: Path | None = None) -> SymbolLifecycleManager:
    return SymbolLifecycleManager()

def create_universe_builder(settings: Settings | None = None, base_dir: Path | None = None) -> InstrumentUniverseBuilder:
    return InstrumentUniverseBuilder(create_instrument_master())

def create_instrument_importer(settings: Settings | None = None, base_dir: Path | None = None) -> InstrumentImporter:
    return InstrumentImporter(create_instrument_master())

def create_corporate_action_importer(settings: Settings | None = None, base_dir: Path | None = None) -> CorporateActionImporter:
    return CorporateActionImporter(None)

def create_price_adjustment_engine(settings: Settings | None = None) -> PriceAdjustmentEngine:
    return PriceAdjustmentEngine()

def create_adjusted_price_service(settings: Settings | None = None, base_dir: Path | None = None) -> AdjustedPriceService:
    return AdjustedPriceService(None, None, create_price_adjustment_engine(), Path("/tmp"))

def create_data_reconciliation_engine(settings: Settings | None = None) -> DataReconciliationEngine:
    return DataReconciliationEngine()
