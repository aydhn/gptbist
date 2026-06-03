from typing import Any, List, Tuple, Optional
from bist_signal_bot.markets.models import MarketNormalizationResult, MarketStatus
from bist_signal_bot.markets.symbols import SymbolNormalizer
import uuid

class MarketDataNormalizer:
    def __init__(self, symbol_normalizer: SymbolNormalizer, market_registry=None):
        self.symbol_normalizer = symbol_normalizer
        self.market_registry = market_registry

    def normalize_row(self, row: dict[str, Any], market_id: str) -> dict[str, Any]:
        res = dict(row)
        res = self.normalize_symbol_field(res, market_id)
        res = self.normalize_currency_field(res, market_id)
        res = self.normalize_datetime_fields(res, market_id)
        res['market_id'] = market_id
        return res

    def normalize_symbol_field(self, row: dict[str, Any], market_id: str) -> dict[str, Any]:
        sym = row.get("symbol")
        if sym:
            row["canonical_symbol"] = self.symbol_normalizer.canonical_symbol(sym, market_id)
        return row

    def normalize_currency_field(self, row: dict[str, Any], market_id: str) -> dict[str, Any]:
        if "currency" not in row:
            def_cur = "TRY"
            if self.market_registry:
                m = self.market_registry.get_market(market_id)
                if m:
                    def_cur = m.default_currency
            row["currency"] = def_cur
        return row

    def normalize_datetime_fields(self, row: dict[str, Any], market_id: str) -> dict[str, Any]:
        # Simple passthrough for MVP
        return row

    def reject_invalid_rows(self, rows: List[dict[str, Any]], market_id: str) -> Tuple[List[dict[str, Any]], int]:
        valid = []
        rejected = 0
        for r in rows:
            if not r.get("symbol"):
                rejected += 1
            else:
                valid.append(r)
        return valid, rejected

    def normalize_dataset(self, rows: List[dict[str, Any]], market_id: str, dataset_type: Optional[str] = None) -> MarketNormalizationResult:
        valid_rows, rejected = self.reject_invalid_rows(rows, market_id)
        output = [self.normalize_row(r, market_id) for r in valid_rows]

        symbols_normalized = len(set(r.get("canonical_symbol") for r in output if "canonical_symbol" in r))

        return MarketNormalizationResult(
            normalization_id=str(uuid.uuid4()),
            market_id=market_id,
            input_rows=len(rows),
            output_rows=len(output),
            normalized_symbols=symbols_normalized,
            rejected_rows=rejected,
            status=MarketStatus.ACTIVE if rejected == 0 else MarketStatus.WATCH
        )
