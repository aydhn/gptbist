from typing import Any, List, Optional
from datetime import datetime
import uuid
from bist_signal_bot.markets.models import MarketValidationResult, MarketStatus
from bist_signal_bot.markets.symbols import SymbolNormalizer
from bist_signal_bot.markets.currencies import CurrencyRegistry
from bist_signal_bot.markets.instruments import InstrumentRegistry

class MarketValidationEngine:
    def __init__(self, symbol_normalizer: SymbolNormalizer, currency_registry: CurrencyRegistry, instrument_registry: InstrumentRegistry):
        self.symbol_normalizer = symbol_normalizer
        self.currency_registry = currency_registry
        self.instrument_registry = instrument_registry

    def status_from_findings(self, findings: List[str]) -> MarketStatus:
        if any("FAIL" in f for f in findings):
            return MarketStatus.FAIL
        if findings:
            return MarketStatus.WATCH
        return MarketStatus.ACTIVE

    def validate_symbols(self, rows: List[dict[str, Any]], market_id: Optional[str] = None) -> List[str]:
        invalid = []
        for r in rows:
            sym = r.get("symbol")
            if sym:
                warnings = self.symbol_normalizer.validate_symbol(sym, market_id)
                if warnings:
                    invalid.append(sym)
        return list(set(invalid))

    def validate_currency(self, rows: List[dict[str, Any]], market_id: Optional[str] = None) -> List[str]:
        invalid = []
        for r in rows:
            cur = r.get("currency")
            if cur:
                warnings = self.currency_registry.validate_currency(cur)
                if warnings:
                    invalid.append(cur)
        return list(set(invalid))

    def validate_calendar_alignment(self, rows: List[dict[str, Any]], market_id: Optional[str] = None) -> List[str]:
        return []

    def validate_instrument_coverage(self, symbols: List[str], market_id: Optional[str] = None) -> List[str]:
        missing = []
        for s in symbols:
            inst = self.instrument_registry.get_instrument(s, market_id)
            if not inst:
                missing.append(s)
        return list(set(missing))

    def validate_market_dataset(self, rows: List[dict[str, Any]], market_id: Optional[str] = None) -> MarketValidationResult:
        symbols = list(set(r.get("symbol") for r in rows if r.get("symbol")))

        invalid_syms = self.validate_symbols(rows, market_id)
        invalid_curs = self.validate_currency(rows, market_id)
        missing_insts = self.validate_instrument_coverage(symbols, market_id)
        cal_warns = self.validate_calendar_alignment(rows, market_id)

        findings = []
        if invalid_syms:
            findings.append(f"Found {len(invalid_syms)} invalid symbols")
        if invalid_curs:
            findings.append(f"FAIL: Found {len(invalid_curs)} invalid currencies")
        if missing_insts:
            findings.append(f"Found {len(missing_insts)} missing instruments")

        status = self.status_from_findings(findings)

        return MarketValidationResult(
            validation_id=str(uuid.uuid4()),
            market_id=market_id,
            created_at=datetime.now(),
            status=status,
            findings=findings,
            missing_instruments=missing_insts,
            invalid_symbols=invalid_syms,
            calendar_warnings=cal_warns
        )
