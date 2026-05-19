from datetime import datetime
from typing import List, Optional
from bist_signal_bot.fundamentals.models import FundamentalFreshnessReport, FundamentalDataStatus
from bist_signal_bot.fundamentals.storage import FundamentalStore
class FundamentalFreshnessChecker:
    def __init__(self, store: FundamentalStore): self.store = store
    def data_status(self, symbol: str, max_age_days: int) -> FundamentalDataStatus: return FundamentalDataStatus.VALID
    def check(self, symbols: List[str], max_age_days: int) -> FundamentalFreshnessReport:
        return FundamentalFreshnessReport(symbols=symbols, stale_symbols=[], missing_symbols=[], fresh_symbols=symbols, max_age_days=max_age_days, generated_at=datetime.now())
