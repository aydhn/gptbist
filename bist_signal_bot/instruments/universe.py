from typing import List, Optional
import uuid
from bist_signal_bot.instruments.models import InstrumentUniverse, UniverseFilter, InstrumentStatus, InstrumentType

class InstrumentUniverseBuilder:
    def __init__(self, master):
        self.master = master

    def build_universe(self, name: str, filter: UniverseFilter) -> InstrumentUniverse:
        symbols = []
        for rec in self.master.list_instruments():
            if filter.include_statuses and rec.status not in filter.include_statuses:
                continue
            if filter.include_types and rec.instrument_type not in filter.include_types:
                continue
            if filter.include_sectors and rec.sector not in filter.include_sectors:
                continue
            if rec.symbol in filter.exclude_symbols:
                continue

            symbols.append(rec.symbol)

        # Add explicitly included
        for sym in filter.include_symbols:
            if sym not in symbols:
                symbols.append(sym)

        return InstrumentUniverse(
            universe_id=str(uuid.uuid4()),
            name=name,
            symbols=symbols,
            filter=filter,
            included_count=len(symbols)
        )

    def default_bist_equity_universe(self) -> InstrumentUniverse:
        f = UniverseFilter(
            include_statuses=[InstrumentStatus.ACTIVE],
            include_types=[InstrumentType.EQUITY]
        )
        return self.build_universe("BIST_EQUITY_DEFAULT", f)

    def sector_universe(self, sector: str) -> InstrumentUniverse:
        f = UniverseFilter(
            include_statuses=[InstrumentStatus.ACTIVE],
            include_sectors=[sector]
        )
        return self.build_universe(f"BIST_SECTOR_{sector.upper()}", f)

    def index_universe(self, index_name: str) -> InstrumentUniverse:
        f = UniverseFilter(
            include_statuses=[InstrumentStatus.ACTIVE]
        )
        # We need custom logic here, simple mock for now
        u = self.build_universe(f"INDEX_{index_name.upper()}", f)
        # Filter further based on master records
        filtered = [s for s in u.symbols if index_name in self.master.get(s).index_memberships]
        u.symbols = filtered
        u.included_count = len(filtered)
        return u

    def apply_liquidity_filter(self, symbols: List[str], min_average_volume: Optional[float]) -> List[str]:
        return symbols

    def exclude_inactive(self, symbols: List[str]) -> List[str]:
        return [s for s in symbols if self.master.get(s) and self.master.get(s).status == InstrumentStatus.ACTIVE]
