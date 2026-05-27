from typing import Any
from bist_signal_bot.financials.models import NormalizedFinancialStatement

class FinancialStatementService:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def get_statements(self, symbol: str, limit: int = 20) -> list[NormalizedFinancialStatement]:
        return []

    def latest_statement(self, symbol: str) -> NormalizedFinancialStatement | None:
        return None

    def statement_by_period(self, symbol: str, fiscal_year: int, fiscal_period: str) -> NormalizedFinancialStatement | None:
        return None

    def available_symbols(self) -> list[str]:
        return []

    def coverage_summary(self) -> dict[str, Any]:
        return {"total_symbols": 0, "total_statements": 0}
