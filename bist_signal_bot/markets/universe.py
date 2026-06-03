from datetime import datetime
from typing import Any, List, Optional
import uuid
from bist_signal_bot.markets.models import MarketUniverse, MarketStatus
from bist_signal_bot.markets.symbols import SymbolNormalizer
from bist_signal_bot.markets.instruments import InstrumentRegistry

class MarketUniverseBuilder:
    def __init__(self, instrument_registry: InstrumentRegistry, symbol_normalizer: SymbolNormalizer, store=None):
        self.instrument_registry = instrument_registry
        self.symbol_normalizer = symbol_normalizer
        self.store = store

    def build_universe(self, name: str, market_id: str, symbols: List[str], filters: Optional[dict[str, Any]] = None) -> MarketUniverse:
        canon_syms = [self.symbol_normalizer.canonical_symbol(s, market_id) for s in symbols]

        inst_ids = []
        for s in canon_syms:
            inst = self.instrument_registry.get_instrument(s, market_id)
            if inst:
                inst_ids.append(inst.instrument_id)

        u = MarketUniverse(
            universe_id=f"{market_id}_{name.upper().replace(' ', '_')}_{str(uuid.uuid4())[:8]}",
            name=name,
            market_id=market_id,
            instrument_ids=inst_ids,
            symbols=canon_syms,
            created_at=datetime.now(),
            filters=filters or {},
            status=MarketStatus.ACTIVE
        )
        if self.store:
            self.store.append_universe(u)
        return u

    def default_universes(self) -> List[MarketUniverse]:
        res = []
        defaults = [
            ("BIST_CORE_RESEARCH", "BIST_EQUITY", ["ASELS", "THYAO", "GARAN", "BIMAS", "EREGL"]),
            ("US_CORE_RESEARCH", "US_EQUITY_RESEARCH", ["AAPL", "MSFT", "SPY"]),
            ("FX_SYNTH_RESEARCH", "FX_RESEARCH", ["USDTRY_SYNTH", "EURUSD_SYNTH"]),
            ("CRYPTO_SYNTH_RESEARCH", "CRYPTO_RESEARCH", ["BTC_SYNTH", "ETH_SYNTH"]),
            ("MACRO_SYNTH_RESEARCH", "MACRO_RESEARCH", ["POLICY_RATE_SYNTH", "INFLATION_SYNTH"]),
            ("SYNTHETIC_FULL_PIPELINE", "SYNTHETIC_RESEARCH", ["SYN_A", "SYN_B"])
        ]

        for name, m_id, syms in defaults:
            res.append(self.build_universe(name, m_id, syms))
        return res

    def universe_for_market(self, market_id: str) -> MarketUniverse:
        if self.store:
            uns = self.store.load_universes(market_id)
            if uns:
                return uns[0]

        defs = self.default_universes()
        for u in defs:
            if u.market_id == market_id:
                return u

        return self.build_universe(f"{market_id}_ALL", market_id, [])

    def validate_universe(self, universe: MarketUniverse) -> List[str]:
        warnings = []
        if not universe.symbols:
            warnings.append("Universe is empty")
        return warnings

    def filter_universe(self, universe: MarketUniverse, filters: dict[str, Any]) -> MarketUniverse:
        return MarketUniverse(
            universe_id=f"{universe.universe_id}_FILTERED",
            name=f"{universe.name} Filtered",
            market_id=universe.market_id,
            instrument_ids=universe.instrument_ids,
            symbols=universe.symbols,
            created_at=datetime.now(),
            filters={**universe.filters, **filters},
            status=universe.status
        )
