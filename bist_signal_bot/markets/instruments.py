from typing import Optional, List
from bist_signal_bot.markets.models import InstrumentDefinition, AssetClass

class InstrumentRegistry:
    def __init__(self, store=None):
        self.store = store
        self._instruments = {}

    def default_instruments(self, market_id: str) -> List[InstrumentDefinition]:
        defaults = {
            "BIST_EQUITY": [
                ("ASELS", "BIST:ASELS"), ("THYAO", "BIST:THYAO"), ("GARAN", "BIST:GARAN"),
                ("BIMAS", "BIST:BIMAS"), ("EREGL", "BIST:EREGL")
            ],
            "US_EQUITY_RESEARCH": [
                ("AAPL", "US:AAPL"), ("MSFT", "US:MSFT"), ("SPY", "US:SPY")
            ],
            "GLOBAL_INDEX_RESEARCH": [("SPX", "INDEX:SPX"), ("XU100_SYNTH", "INDEX:XU100_SYNTH")],
            "FX_RESEARCH": [("USDTRY_SYNTH", "FX:USDTRY_SYNTH"), ("EURUSD_SYNTH", "FX:EURUSD_SYNTH")],
            "CRYPTO_RESEARCH": [("BTC_SYNTH", "CRYPTO:BTC_SYNTH"), ("ETH_SYNTH", "CRYPTO:ETH_SYNTH")],
            "MACRO_RESEARCH": [("POLICY_RATE_SYNTH", "MACRO:POLICY_RATE_SYNTH"), ("INFLATION_SYNTH", "MACRO:INFLATION_SYNTH")]
        }
        res = []
        if market_id in defaults:
            for i, (sym, canon) in enumerate(defaults[market_id]):
                res.append(InstrumentDefinition(
                    instrument_id=f"{market_id}_{sym}",
                    market_id=market_id,
                    symbol=sym,
                    canonical_symbol=canon,
                    asset_class=AssetClass.EQUITY if "EQUITY" in market_id else AssetClass.CUSTOM,
                    currency="TRY" if market_id == "BIST_EQUITY" else "USD",
                    active=True
                ))
        return res

    def list_instruments(self, market_id: Optional[str] = None, active: Optional[bool] = None) -> List[InstrumentDefinition]:
        if not self._instruments and market_id:
            for inst in self.default_instruments(market_id):
                self._instruments[inst.instrument_id] = inst
        res = list(self._instruments.values())
        if market_id:
            res = [i for i in res if i.market_id == market_id]
        if active is not None:
            res = [i for i in res if i.active == active]
        return res

    def get_instrument(self, symbol_or_id: str, market_id: Optional[str] = None) -> Optional[InstrumentDefinition]:
        for i in self.list_instruments(market_id):
            if i.instrument_id == symbol_or_id or i.symbol == symbol_or_id or i.canonical_symbol == symbol_or_id:
                return i
        return None

    def register_instrument(self, instrument: InstrumentDefinition, confirm: bool = False) -> InstrumentDefinition:
        self._instruments[instrument.instrument_id] = instrument
        if confirm and self.store:
            self.store.append_instruments([instrument])
        return instrument

    def validate_instrument(self, instrument: InstrumentDefinition) -> List[str]:
        warnings = []
        if not instrument.symbol:
            warnings.append("Symbol is empty")
        if not instrument.canonical_symbol:
            warnings.append("Canonical symbol is empty")
        return warnings

    def instrument_summary(self, instrument: InstrumentDefinition) -> dict:
        return {
            "instrument_id": instrument.instrument_id,
            "market_id": instrument.market_id,
            "canonical_symbol": instrument.canonical_symbol,
            "active": instrument.active,
            "disclaimer": instrument.disclaimer
        }
