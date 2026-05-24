from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
from bist_signal_bot.instruments.models import InstrumentRecord, InstrumentStatus
from bist_signal_bot.data.reconciliation import DataQualityIssue, DataIssueType, DataIssueSeverity

logger = logging.getLogger(__name__)

class InstrumentMaster:
    def __init__(self):
        self._records: Dict[str, InstrumentRecord] = {}

    def upsert_instrument(self, record: InstrumentRecord, confirm_overwrite: bool = False) -> InstrumentRecord:
        if record.symbol in self._records and not confirm_overwrite:
            logger.warning(f"Instrument {record.symbol} already exists. Skipping overwrite. Use confirm_overwrite=True")
            return self._records[record.symbol]

        self._records[record.symbol] = record
        return record

    def get(self, symbol: str) -> Optional[InstrumentRecord]:
        return self._records.get(symbol.upper())

    def resolve_symbol(self, symbol_or_alias: str, as_of: Optional[datetime] = None) -> Optional[str]:
        target = symbol_or_alias.upper()
        if target in self._records:
            return target

        for symbol, record in self._records.items():
            if target in record.aliases or target in record.previous_symbols:
                return symbol

        return None

    def list_instruments(self, status: Optional[InstrumentStatus] = None, sector: Optional[str] = None, limit: int = 1000) -> List[InstrumentRecord]:
        results = []
        for record in self._records.values():
            if status and record.status != status:
                continue
            if sector and record.sector != sector:
                continue
            results.append(record)
        return results[:limit]

    def active_symbols(self, include_etf: bool = False) -> List[str]:
        return [
            sym for sym, rec in self._records.items()
            if rec.status == InstrumentStatus.ACTIVE and (include_etf or rec.instrument_type.name != 'ETF')
        ]

    def validate_master(self) -> List[DataQualityIssue]:
        issues = []
        # Basic validation: check for duplicate ISINs
        seen_isins = {}
        for symbol, record in self._records.items():
            if record.isin:
                if record.isin in seen_isins:
                    issues.append(DataQualityIssue(
                        issue_id=f"dup_isin_{record.isin}_{symbol}",
                        symbol=symbol,
                        issue_type=DataIssueType.UNKNOWN,
                        severity=DataIssueSeverity.MEDIUM,
                        message=f"Duplicate ISIN {record.isin} found for {symbol} and {seen_isins[record.isin]}",
                    ))
                else:
                    seen_isins[record.isin] = symbol
        return issues

    def snapshot(self) -> Dict[str, Any]:
        return {
            "count": len(self._records),
            "active_count": len(self.active_symbols()),
            "timestamp": datetime.utcnow().isoformat()
        }
