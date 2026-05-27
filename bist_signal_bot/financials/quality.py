import uuid
from bist_signal_bot.financials.models import (
    NormalizedFinancialStatement,
    EarningsQualityAssessment,
    FinancialQualityStatus
)

class EarningsQualityAnalyzer:
    def __init__(self, settings=None):
        self.settings = settings
        self.strong_score = getattr(settings, "FINANCIAL_QUALITY_STRONG_SCORE", 70.0) if settings else 70.0
        self.weak_score = getattr(settings, "FINANCIAL_QUALITY_WEAK_SCORE", 40.0) if settings else 40.0
        self.debt_warn = getattr(settings, "FINANCIAL_HIGH_DEBT_TO_EQUITY_WARN", 2.0) if settings else 2.0

    def assess_quality(self, statement: NormalizedFinancialStatement, statements: list[NormalizedFinancialStatement] | None = None) -> EarningsQualityAssessment:
        warnings = []
        strengths = []
        weaknesses = []

        cash_conv = self.cash_conversion_quality(statement)
        debt_q = self.debt_quality(statement)

        if cash_conv is not None:
            if cash_conv > 80:
                strengths.append("Strong cash conversion")
            elif cash_conv < 40:
                weaknesses.append("Weak cash conversion")
                warnings.append("OCF significantly trails Net Income")

        if debt_q is not None:
            if debt_q < 40:
                weaknesses.append("High debt burden")
                warnings.append(f"High debt-to-equity ratio")

        scores = {
            "cash_conversion": cash_conv,
            "debt": debt_q
        }

        overall = self.overall_quality(scores)
        status = self.classify_quality(overall)

        return EarningsQualityAssessment(
            assessment_id=str(uuid.uuid4()),
            symbol=statement.symbol,
            fiscal_year=statement.fiscal_year,
            fiscal_period=statement.fiscal_period,
            period_end=statement.period_end,
            status=status,
            key_strengths=strengths,
            key_weaknesses=weaknesses,
            warnings=warnings,
            metadata={},
            cash_conversion_score=cash_conv,
            debt_quality_score=debt_q,
            overall_quality_score=overall
        )

    def cash_conversion_quality(self, statement: NormalizedFinancialStatement) -> float | None:
        if statement.operating_cash_flow is not None and statement.net_income is not None and statement.net_income > 0:
            ratio = statement.operating_cash_flow / statement.net_income
            # Map ratio to 0-100 score
            score = max(0.0, min(100.0, ratio * 100))
            return score
        return None

    def debt_quality(self, statement: NormalizedFinancialStatement) -> float | None:
        if statement.total_debt is not None and statement.total_equity is not None and statement.total_equity > 0:
            ratio = statement.total_debt / statement.total_equity
            if ratio > self.debt_warn:
                return 20.0
            elif ratio > 1.0:
                return 50.0
            return 80.0
        return None

    def overall_quality(self, scores: dict[str, float | None]) -> float | None:
        valid_scores = [s for s in scores.values() if s is not None]
        if not valid_scores:
            return None
        return sum(valid_scores) / len(valid_scores)

    def classify_quality(self, score: float | None) -> FinancialQualityStatus:
        if score is None:
            return FinancialQualityStatus.INSUFFICIENT_DATA
        if score >= self.strong_score:
            return FinancialQualityStatus.STRONG
        if score <= self.weak_score:
            return FinancialQualityStatus.WEAK
        return FinancialQualityStatus.WATCH
