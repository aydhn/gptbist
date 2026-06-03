from typing import Optional, List
from bist_signal_bot.markets.models import SymbolMapping

class SymbolNormalizer:
    def __init__(self, store=None):
        self.store = store

    def strip_exchange_suffix(self, symbol: str) -> str:
        s = symbol.strip().upper()
        if s.endswith(".IS"):
            return s[:-3]
        if s.endswith(".O"):
            return s[:-2]
        return s

    def detect_market(self, raw_symbol: str) -> Optional[str]:
        s = raw_symbol.upper()
        if s.endswith(".IS"):
            return "BIST_EQUITY"
        if s in ["AAPL", "MSFT", "SPY"] or s.endswith(".O"):
            return "US_EQUITY_RESEARCH"
        if "USDTRY" in s or "EURUSD" in s:
            return "FX_RESEARCH"
        if "BTC" in s or "ETH" in s:
            return "CRYPTO_RESEARCH"
        if "SPX" in s or "XU100" in s:
            return "GLOBAL_INDEX_RESEARCH"
        return None

    def canonicalize(self, raw_symbol: str, market_id: Optional[str] = None) -> SymbolMapping:
        warnings = []
        clean = self.strip_exchange_suffix(raw_symbol)

        # Simple turkish char detection for warning
        if any(c in clean for c in "ÇĞİÖŞÜ"):
            warnings.append("Symbol contains Turkish characters. Consider normalizing.")
            clean = clean.replace('Ç', 'C').replace('Ğ', 'G').replace('İ', 'I').replace('Ö', 'O').replace('Ş', 'S').replace('Ü', 'U')

        m_id = market_id or self.detect_market(raw_symbol) or "UNKNOWN"
        prefix = m_id.split('_')[0] if m_id != "UNKNOWN" else "UNKNOWN"

        canon = f"{prefix}:{clean}"

        return SymbolMapping(
            mapping_id=f"{m_id}_{clean}",
            raw_symbol=raw_symbol,
            canonical_symbol=canon,
            market_id=m_id,
            normalized=True,
            warnings=warnings
        )

    def canonical_symbol(self, raw_symbol: str, market_id: Optional[str] = None) -> str:
        return self.canonicalize(raw_symbol, market_id).canonical_symbol

    def normalize_many(self, symbols: List[str], market_id: Optional[str] = None) -> List[SymbolMapping]:
        return [self.canonicalize(s, market_id) for s in symbols]

    def validate_symbol(self, symbol: str, market_id: Optional[str] = None) -> List[str]:
        mapping = self.canonicalize(symbol, market_id)
        return mapping.warnings
