import uuid
from bist_signal_bot.financials.models import (
    NormalizedFinancialStatement,
    FinancialRatio,
    FinancialMetricDirection,
    FinancialQualityStatus
)

class FinancialRatioCalculator:
    def __init__(self, settings=None):
        self.settings = settings
        self.eps = getattr(settings, "FINANCIAL_RATIO_MIN_DENOMINATOR_ABS", 1e-9) if settings else 1e-9

    def calculate_ratios(self, statement: NormalizedFinancialStatement) -> list[FinancialRatio]:
        ratios = []
        ratios.append(self.gross_margin(statement))
        ratios.append(self.operating_margin(statement))
        ratios.append(self.ebitda_margin(statement))
        ratios.append(self.net_margin(statement))
        ratios.append(self.debt_to_equity(statement))
        # Add other ratios here...

        # Filter out None values
        return [r for r in ratios if r is not None]

    def _create_ratio(self, statement, name, value, direction) -> FinancialRatio | None:
        if value is None:
            return None
        return FinancialRatio(
            ratio_id=str(uuid.uuid4()),
            symbol=statement.symbol,
            fiscal_year=statement.fiscal_year,
            fiscal_period=statement.fiscal_period,
            period_end=statement.period_end,
            name=name,
            value=value,
            direction=direction,
            status=FinancialQualityStatus.UNKNOWN,
            warnings=[],
            metadata={}
        )

    def gross_margin(self, statement: NormalizedFinancialStatement) -> FinancialRatio | None:
        if statement.gross_profit is not None and statement.revenue is not None and abs(statement.revenue) > self.eps:
            return self._create_ratio(statement, "gross_margin", statement.gross_profit / statement.revenue, FinancialMetricDirection.HIGHER_IS_BETTER)
        return None

    def operating_margin(self, statement: NormalizedFinancialStatement) -> FinancialRatio | None:
        if statement.operating_profit is not None and statement.revenue is not None and abs(statement.revenue) > self.eps:
            return self._create_ratio(statement, "operating_margin", statement.operating_profit / statement.revenue, FinancialMetricDirection.HIGHER_IS_BETTER)
        return None

    def ebitda_margin(self, statement: NormalizedFinancialStatement) -> FinancialRatio | None:
        if statement.ebitda is not None and statement.revenue is not None and abs(statement.revenue) > self.eps:
            return self._create_ratio(statement, "ebitda_margin", statement.ebitda / statement.revenue, FinancialMetricDirection.HIGHER_IS_BETTER)
        return None

    def net_margin(self, statement: NormalizedFinancialStatement) -> FinancialRatio | None:
        if statement.net_income is not None and statement.revenue is not None and abs(statement.revenue) > self.eps:
            return self._create_ratio(statement, "net_margin", statement.net_income / statement.revenue, FinancialMetricDirection.HIGHER_IS_BETTER)
        return None

    def debt_to_equity(self, statement: NormalizedFinancialStatement) -> FinancialRatio | None:
        if statement.total_debt is not None and statement.total_equity is not None and abs(statement.total_equity) > self.eps:
            ratio = self._create_ratio(statement, "debt_to_equity", statement.total_debt / statement.total_equity, FinancialMetricDirection.LOWER_IS_BETTER)
            if ratio and statement.total_equity < 0:
                ratio.warnings.append("Negative total_equity")
            return ratio
        return None
