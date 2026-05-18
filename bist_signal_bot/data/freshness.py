from typing import List, Optional
from datetime import datetime
from bist_signal_bot.data.providers_v2.models import FreshnessReport, DataLineageSource
from bist_signal_bot.data.providers_v2.lineage import DataLineageStore

class DataFreshnessChecker:
    def __init__(self, lineage_store: Optional[DataLineageStore] = None):
        self.lineage_store = lineage_store or DataLineageStore()

    def check_symbols(self, symbols: List[str], timeframe: str, max_age_hours: float) -> FreshnessReport:
        fresh = []
        stale = []
        missing = []
        total_age = 0.0
        count = 0
        warnings = []

        for symbol in symbols:
            lineage = self.lineage_store.latest_for_symbol(symbol, timeframe)
            if not lineage:
                missing.append(symbol)
                warnings.append(f"No lineage found for {symbol} ({timeframe})")
                continue

            age = self.age_hours_from_lineage(lineage)
            if age is None:
                missing.append(symbol)
                warnings.append(f"Invalid fetch date for {symbol} ({timeframe})")
                continue

            total_age += age
            count += 1

            if self.is_fresh(lineage, max_age_hours):
                fresh.append(symbol)
            else:
                stale.append(symbol)

        avg_age = total_age / count if count > 0 else None

        if stale:
            warnings.append(f"Found {len(stale)} stale symbols.")
        if missing:
            warnings.append(f"Found {len(missing)} missing symbols.")

        return FreshnessReport(
            symbols=symbols,
            timeframe=timeframe,
            max_age_hours=max_age_hours,
            fresh_symbols=fresh,
            stale_symbols=stale,
            missing_symbols=missing,
            average_age_hours=avg_age,
            warnings=warnings
        )

    def age_hours_from_lineage(self, lineage: Optional[DataLineageSource]) -> Optional[float]:
        if not lineage or not lineage.fetched_at:
            return None
        age = (datetime.utcnow().replace(tzinfo=None) - lineage.fetched_at.replace(tzinfo=None)).total_seconds() / 3600
        return max(0.0, age)

    def is_fresh(self, lineage: Optional[DataLineageSource], max_age_hours: float) -> bool:
        age = self.age_hours_from_lineage(lineage)
        if age is None:
            return False
        return age <= max_age_hours
