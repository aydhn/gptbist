import os
from pathlib import Path

base_dir = Path("bist_signal_bot")

# 9. financials/ratios.py
with open(base_dir / "financials" / "ratios.py", "w") as f:
    f.write('''import uuid
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
''')

# 10. financials/trends.py
with open(base_dir / "financials" / "trends.py", "w") as f:
    f.write('''import uuid
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
''')

# 11. financials/quality.py
with open(base_dir / "financials" / "quality.py", "w") as f:
    f.write('''import uuid
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
''')

# 12. financials/sector_compare.py
with open(base_dir / "financials" / "sector_compare.py", "w") as f:
    f.write('''import uuid
from datetime import datetime
import statistics
from bist_signal_bot.financials.models import (
    NormalizedFinancialStatement,
    FinancialRatio,
    SectorFinancialComparison,
    FinancialQualityStatus
)

class SectorFinancialComparator:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def compare_symbol(self, symbol: str, statements: list[NormalizedFinancialStatement], ratios_by_symbol: dict[str, list[FinancialRatio]]) -> SectorFinancialComparison:
        # Mock sector for now
        sector = "MOCK_SECTOR"

        symbol_ratios = ratios_by_symbol.get(symbol, [])
        medians = self.sector_medians(sector, ratios_by_symbol)

        ranks = {}
        for r in symbol_ratios:
            peers = []
            for sym, s_ratios in ratios_by_symbol.items():
                for sr in s_ratios:
                    if sr.name == r.name and sr.value is not None:
                        peers.append(sr.value)
            ranks[r.name] = self.percentile_rank(r.value, peers)

        sw = self.relative_strengths_weaknesses(symbol_ratios, medians)
        score = self.sector_score(ranks)

        return SectorFinancialComparison(
            comparison_id=str(uuid.uuid4()),
            symbol=symbol,
            period_end=datetime.now(),
            ratios=symbol_ratios,
            sector_medians=medians,
            percentile_ranks=ranks,
            relative_strengths=sw.get("strengths", []),
            relative_weaknesses=sw.get("weaknesses", []),
            status=FinancialQualityStatus.UNKNOWN,
            warnings=[],
            metadata={},
            sector=sector,
            sector_score=score
        )

    def sector_medians(self, sector: str, ratios_by_symbol: dict[str, list[FinancialRatio]]) -> dict[str, float | None]:
        medians = {}
        # Aggregate by name
        values_by_name = {}
        for sym, ratios in ratios_by_symbol.items():
            for r in ratios:
                if r.value is not None:
                    if r.name not in values_by_name:
                        values_by_name[r.name] = []
                    values_by_name[r.name].append(r.value)

        for name, vals in values_by_name.items():
            if vals:
                medians[name] = statistics.median(vals)
        return medians

    def percentile_rank(self, value: float | None, peers: list[float]) -> float | None:
        if value is None or not peers:
            return None
        less_than = sum(1 for p in peers if p < value)
        return (less_than / len(peers)) * 100

    def relative_strengths_weaknesses(self, symbol_ratios: list[FinancialRatio], medians: dict[str, float | None]) -> dict[str, list[str]]:
        strengths = []
        weaknesses = []

        for r in symbol_ratios:
            med = medians.get(r.name)
            if r.value is not None and med is not None:
                # Basic mock logic
                if r.value > med * 1.2:
                    strengths.append(f"{r.name} above sector median")
                elif r.value < med * 0.8:
                    weaknesses.append(f"{r.name} below sector median")

        return {"strengths": strengths, "weaknesses": weaknesses}

    def sector_score(self, percentile_ranks: dict[str, float | None]) -> float | None:
        valid = [v for v in percentile_ranks.values() if v is not None]
        if not valid:
            return None
        return sum(valid) / len(valid)
''')
