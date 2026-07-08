import uuid
from datetime import datetime
from bist_signal_bot.breadth.models import BreadthScope, BreadthUniverseSnapshot
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.instruments.master import InstrumentMaster
from bist_signal_bot.core.exceptions import BreadthUniverseError

class BreadthUniverseBuilder:
    def __init__(self, settings: Settings | None = None, instrument_master: InstrumentMaster | None = None):
        self.settings = settings or Settings()
        self.instrument_master = instrument_master or InstrumentMaster(self.settings)

    def build_universe(
        self, name: str | None = None, symbols: list[str] | None = None, scope: BreadthScope = BreadthScope.MARKET
    ) -> BreadthUniverseSnapshot:
        universe_name = name or self.settings.BREADTH_DEFAULT_UNIVERSE_NAME

        if symbols is None:
            active_instruments = self.instrument_master.get_all_active()
            symbols_to_process = [inst.symbol for inst in active_instruments]
        else:
            symbols_to_process = symbols

        active_symbols = self.filter_active_symbols(symbols_to_process)
        valid_symbols, excluded_symbols = self.exclude_invalid_symbols(active_symbols)

        sectors = self.sector_map(valid_symbols)

        warnings = []
        if len(valid_symbols) < self.settings.BREADTH_MIN_UNIVERSE_SIZE:
            warnings.append(f"Universe size ({len(valid_symbols)}) is below minimum threshold ({self.settings.BREADTH_MIN_UNIVERSE_SIZE}).")

        return BreadthUniverseSnapshot(
            universe_id=str(uuid.uuid4()),
            name=universe_name,
            as_of=datetime.now(),
            scope=scope,
            symbols=valid_symbols,
            sectors=sectors,
            active_count=len(valid_symbols),
            excluded_symbols=excluded_symbols,
            warnings=warnings
        )

    def filter_active_symbols(self, symbols: list[str]) -> list[str]:
        if not self.settings.BREADTH_EXCLUDE_INACTIVE_SYMBOLS:
            return symbols

        active_symbols = []
        if not symbols:
            return active_symbols

        instruments = self.instrument_master.get_instruments(symbols)
        for symbol, inst in zip(symbols, instruments):
            if inst and inst.is_active:
                active_symbols.append(symbol)
        return active_symbols

    def sector_map(self, symbols: list[str]) -> dict[str, str]:
        sector_mapping = {}
        if not symbols:
            return sector_mapping

        instruments = self.instrument_master.get_instruments(symbols)
        for symbol, inst in zip(symbols, instruments):
            sector = inst.sector if inst and inst.sector else "UNKNOWN"
            sector_mapping[symbol] = sector
        return sector_mapping

    def exclude_invalid_symbols(self, symbols: list[str]) -> tuple[list[str], list[str]]:
        valid = []
        excluded = []
        for symbol in symbols:
            if not symbol or not isinstance(symbol, str):
                excluded.append(str(symbol))
            else:
                valid.append(symbol.upper())
        return valid, excluded
