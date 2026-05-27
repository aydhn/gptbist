from bist_signal_bot.financials.models import NormalizedFinancialStatement
from datetime import datetime

class FinancialPeriodEngine:
    def __init__(self, settings=None):
        self.settings = settings

    def sort_periods(self, statements: list[NormalizedFinancialStatement]) -> list[NormalizedFinancialStatement]:
        return sorted(statements, key=lambda s: (s.fiscal_year, s.fiscal_period))

    def previous_period(self, statement: NormalizedFinancialStatement, statements: list[NormalizedFinancialStatement]) -> NormalizedFinancialStatement | None:
        sorted_stmts = self.sort_periods(statements)
        idx = -1
        for i, s in enumerate(sorted_stmts):
            if s.normalized_id == statement.normalized_id:
                idx = i
                break

        if idx > 0:
            return sorted_stmts[idx - 1]
        return None

    def same_period_previous_year(self, statement: NormalizedFinancialStatement, statements: list[NormalizedFinancialStatement]) -> NormalizedFinancialStatement | None:
        target_year = statement.fiscal_year - 1
        for s in statements:
            if s.fiscal_year == target_year and s.fiscal_period == statement.fiscal_period:
                return s
        return None

    def build_ttm(self, symbol: str, statements: list[NormalizedFinancialStatement], as_of: datetime | None = None) -> NormalizedFinancialStatement | None:
        # Simplified TTM implementation
        sorted_stmts = self.sort_periods([s for s in statements if s.symbol == symbol])
        if not sorted_stmts:
            return None

        latest = sorted_stmts[-1]
        # In a real scenario, this would aggregate the last 4 quarters
        # For now, return the latest statement as a placeholder for TTM
        return latest

    def period_key(self, statement: NormalizedFinancialStatement) -> str:
        return f"{statement.fiscal_year}-{statement.fiscal_period}"
