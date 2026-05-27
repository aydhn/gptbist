import uuid
from bist_signal_bot.financials.models import (
    NormalizedFinancialStatement,
    FinancialTrendMetric,
    FinancialQualityStatus
)
from bist_signal_bot.financials.periods import FinancialPeriodEngine

class FinancialTrendAnalyzer:
    def __init__(self, settings=None):
        self.settings = settings
        self.period_engine = FinancialPeriodEngine(settings)

    def analyze_trends(self, symbol: str, statements: list[NormalizedFinancialStatement]) -> list[FinancialTrendMetric]:
        if not statements:
            return []

        current = self.period_engine.sort_periods(statements)[-1]

        metrics = ["revenue", "gross_profit", "ebitda", "net_income", "operating_cash_flow", "total_debt", "total_equity"]
        trends = []
        for m in metrics:
            trend = self.metric_trend(m, current, statements)
            if trend:
                trends.append(trend)
        return trends

    def metric_trend(self, metric_name: str, current: NormalizedFinancialStatement, statements: list[NormalizedFinancialStatement]) -> FinancialTrendMetric | None:
        curr_val = getattr(current, metric_name, None)
        prev = self.period_engine.previous_period(current, statements)
        prev_yr = self.period_engine.same_period_previous_year(current, statements)

        prev_val = getattr(prev, metric_name, None) if prev else None
        prev_yr_val = getattr(prev_yr, metric_name, None) if prev_yr else None

        yoy = self.yoy_change(curr_val, prev_yr_val)
        qoq = self.qoq_change(curr_val, prev_val)

        score = self.trend_score(metric_name, yoy, qoq)

        if curr_val is None:
            return None

        return FinancialTrendMetric(
            trend_id=str(uuid.uuid4()),
            symbol=current.symbol,
            metric_name=metric_name,
            period_end=current.period_end,
            status=FinancialQualityStatus.UNKNOWN,
            warnings=[],
            metadata={},
            current_value=curr_val,
            previous_value=prev_val,
            yoy_change_pct=yoy,
            qoq_change_pct=qoq,
            ttm_value=None, # Implement TTM logic later
            trend_score=score
        )

    def yoy_change(self, current_value: float | None, previous_year_value: float | None) -> float | None:
        if current_value is not None and previous_year_value is not None and abs(previous_year_value) > 1e-9:
            return (current_value - previous_year_value) / abs(previous_year_value)
        return None

    def qoq_change(self, current_value: float | None, previous_value: float | None) -> float | None:
        if current_value is not None and previous_value is not None and abs(previous_value) > 1e-9:
            return (current_value - previous_value) / abs(previous_value)
        return None

    def trend_score(self, metric_name: str, yoy: float | None, qoq: float | None) -> float | None:
        # Simple scoring logic
        if yoy is None and qoq is None:
            return None

        score = 50.0
        if yoy is not None:
            if yoy > 0:
                score += min(yoy * 100, 25)
            else:
                score += max(yoy * 100, -25)

        if metric_name == "total_debt":
            # Reverse score for debt
            score = 100 - score

        return max(0.0, min(100.0, score))
