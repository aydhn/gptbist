import pandas as pd
from datetime import datetime
from typing import Any, Optional, Tuple
from bist_signal_bot.fundamentals.models import FundamentalImportRequest, FinancialStatementRecord, CorporateEvent, SectorClassification, FinancialStatementType, FinancialPeriodType, CorporateEventType

class FundamentalNormalizer:
    @staticmethod
    def parse_period(value: Any) -> Tuple[int, Optional[int], FinancialPeriodType]:
        return 0, None, FinancialPeriodType.ANNUAL
    @staticmethod
    def parse_date(value: Any) -> Optional[datetime]:
        try: return pd.to_datetime(value).to_pydatetime()
        except: return None
    @staticmethod
    def normalize_numeric(value: Any) -> Optional[float]:
        try: return float(value)
        except: return None
    def normalize_statement_dataframe(self, df: pd.DataFrame, request: FundamentalImportRequest) -> list[FinancialStatementRecord]:
        records = []
        cols = {c.lower(): c for c in df.columns}
        sym_col = cols.get("symbol", cols.get("sembol", cols.get("kod")))
        end_col = cols.get("period_end_date", cols.get("donem_sonu", cols.get("dönem_sonu", "date")))
        for row in df.itertuples(index=False):
            sym = getattr(row, sym_col) if sym_col else request.symbol
            if not sym: continue
            end_date_raw = getattr(row, end_col) if end_col else None
            end_date = self.parse_date(end_date_raw) if end_date_raw else None
            if not end_date: continue
            records.append(FinancialStatementRecord(record_id=f"{sym}", symbol=str(sym), statement_type=request.statement_type or FinancialStatementType.UNKNOWN, period_type=request.period_type or FinancialPeriodType.UNKNOWN, fiscal_year=end_date.year, period_end_date=end_date, currency="TRY", values={}, imported_at=datetime.now()))
        return records
    def normalize_events_dataframe(self, df, request): return []
    def normalize_sector_dataframe(self, df, request): return []
