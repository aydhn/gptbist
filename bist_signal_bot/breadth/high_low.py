import uuid
from datetime import datetime
from bist_signal_bot.breadth.models import BreadthInputRow, BreadthScope, BreadthStatus, HighLowBreadthSummary
from bist_signal_bot.config.settings import Settings

class HighLowBreadthAnalyzer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def analyze(self, inputs: list[BreadthInputRow], scope: BreadthScope, scope_name: str) -> HighLowBreadthSummary:
        if not inputs:
            return HighLowBreadthSummary(
                highlow_id=str(uuid.uuid4()),
                scope=scope,
                scope_name=scope_name,
                as_of=datetime.now(),
                new_high_20d_count=0,
                new_low_20d_count=0,
                new_high_52w_count=0,
                new_low_52w_count=0,
                high_low_spread=0,
                status=BreadthStatus.INSUFFICIENT_DATA,
                warnings=["Empty inputs provided for high/low calculation."]
            )

        as_of = inputs[0].as_of if inputs else datetime.now()

        nh_20 = 0
        nl_20 = 0
        nh_52 = 0
        nl_52 = 0

        warnings = set()

        for row in inputs:
            if self.is_new_high(row, "high_20d"): nh_20 += 1
            if self.is_new_low(row, "low_20d"): nl_20 += 1
            if self.is_new_high(row, "high_252d"): nh_52 += 1
            if self.is_new_low(row, "low_252d"): nl_52 += 1

            if row.high_252d is None or row.low_252d is None:
                warnings.add("Missing 52w high/low data for some symbols.")

        spread = nh_52 - nl_52

        summary = HighLowBreadthSummary(
            highlow_id=str(uuid.uuid4()),
            scope=scope,
            scope_name=scope_name,
            as_of=as_of,
            new_high_20d_count=nh_20,
            new_low_20d_count=nl_20,
            new_high_52w_count=nh_52,
            new_low_52w_count=nl_52,
            high_low_spread=spread,
            warnings=list(warnings)
        )

        summary.high_low_score = self.high_low_score(summary)
        summary.status = self.classify_high_low(summary.high_low_score)

        return summary

    def is_new_high(self, row: BreadthInputRow, field: str) -> bool:
        if row.close is None:
            return False
        val = getattr(row, field, None)
        if val is None:
            return False
        # Simplistic check: if close >= rolling high
        return row.close >= val

    def is_new_low(self, row: BreadthInputRow, field: str) -> bool:
        if row.close is None:
            return False
        val = getattr(row, field, None)
        if val is None:
            return False
        return row.close <= val

    def high_low_score(self, summary: HighLowBreadthSummary) -> float | None:
        total = summary.new_high_52w_count + summary.new_low_52w_count
        if total == 0:
            return 50.0 # Neutral if no highs or lows
        return round((summary.new_high_52w_count / total) * 100.0, 2)

    def classify_high_low(self, score: float | None) -> BreadthStatus:
        if score is None:
            return BreadthStatus.UNKNOWN
        if score >= 80.0:
            return BreadthStatus.STRONG
        elif score >= 60.0:
            return BreadthStatus.POSITIVE
        elif score <= 20.0:
            return BreadthStatus.WEAK
        elif score <= 40.0:
            return BreadthStatus.NEGATIVE
        return BreadthStatus.NEUTRAL
