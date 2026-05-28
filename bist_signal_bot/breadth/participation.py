import uuid
from datetime import datetime
from bist_signal_bot.breadth.models import BreadthInputRow, BreadthScope, BreadthStatus, ParticipationSummary
from bist_signal_bot.config.settings import Settings

class ParticipationAnalyzer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def analyze(self, inputs: list[BreadthInputRow], scope: BreadthScope, scope_name: str) -> ParticipationSummary:
        if not inputs:
            return ParticipationSummary(
                participation_id=str(uuid.uuid4()),
                scope=scope,
                scope_name=scope_name,
                as_of=datetime.now(),
                status=BreadthStatus.INSUFFICIENT_DATA,
                warnings=["Empty inputs provided for participation calculation."]
            )

        as_of = inputs[0].as_of if inputs else datetime.now()

        above_ma_20_pct = self.above_ma_pct(inputs, "ma_20")
        above_ma_50_pct = self.above_ma_pct(inputs, "ma_50")
        above_ma_200_pct = self.above_ma_pct(inputs, "ma_200")
        pos_ret_pct = self.positive_return_pct(inputs)

        warnings = []
        if above_ma_20_pct is None and above_ma_50_pct is None and above_ma_200_pct is None:
            warnings.append("No moving average data available for participation score.")

        summary = ParticipationSummary(
            participation_id=str(uuid.uuid4()),
            scope=scope,
            scope_name=scope_name,
            as_of=as_of,
            above_ma_20_pct=above_ma_20_pct,
            above_ma_50_pct=above_ma_50_pct,
            above_ma_200_pct=above_ma_200_pct,
            positive_return_pct=pos_ret_pct,
            breadth_thrust_score=self.breadth_thrust_score(inputs),
            warnings=warnings
        )
        summary.participation_score = self.participation_score(summary)
        summary.status = self.classify_participation(summary.participation_score)

        if len(inputs) < self.settings.BREADTH_MIN_UNIVERSE_SIZE:
            summary.status = BreadthStatus.INSUFFICIENT_DATA
            summary.warnings.append(f"Universe size below minimum ({self.settings.BREADTH_MIN_UNIVERSE_SIZE})")

        return summary

    def above_ma_pct(self, inputs: list[BreadthInputRow], ma_field: str) -> float | None:
        count = 0
        valid_total = 0
        for row in inputs:
            ma_val = getattr(row, ma_field, None)
            if row.close is not None and ma_val is not None:
                valid_total += 1
                if row.close > ma_val:
                    count += 1

        if valid_total == 0:
            return None
        return round((count / valid_total) * 100.0, 2)

    def positive_return_pct(self, inputs: list[BreadthInputRow]) -> float | None:
        count = 0
        valid_total = 0
        for row in inputs:
            if row.return_1d_pct is not None:
                valid_total += 1
                if row.return_1d_pct > 0:
                    count += 1

        if valid_total == 0:
            return None
        return round((count / valid_total) * 100.0, 2)

    def breadth_thrust_score(self, inputs: list[BreadthInputRow]) -> float | None:
        # Simplistic proxy: percent of symbols with return > 1.0% in a single day
        count = 0
        valid_total = 0
        for row in inputs:
            if row.return_1d_pct is not None:
                valid_total += 1
                if row.return_1d_pct > 1.0:
                    count += 1
        if valid_total == 0:
            return None
        return round((count / valid_total) * 100.0, 2)

    def participation_score(self, summary: ParticipationSummary) -> float | None:
        scores = []
        if summary.above_ma_20_pct is not None: scores.append(summary.above_ma_20_pct)
        if summary.above_ma_50_pct is not None: scores.append(summary.above_ma_50_pct)
        if summary.above_ma_200_pct is not None: scores.append(summary.above_ma_200_pct)

        if not scores:
            return None

        # Weighted average or simple average. Using simple average for now.
        return round(sum(scores) / len(scores), 2)

    def classify_participation(self, score: float | None) -> BreadthStatus:
        if score is None:
            return BreadthStatus.UNKNOWN
        if score >= self.settings.BREADTH_STRONG_THRESHOLD:
            return BreadthStatus.STRONG
        elif score >= 50.0:
            return BreadthStatus.POSITIVE
        elif score <= self.settings.BREADTH_WEAK_THRESHOLD:
            return BreadthStatus.WEAK
        elif score <= self.settings.BREADTH_LOW_PARTICIPATION_THRESHOLD:
            return BreadthStatus.NEGATIVE
        return BreadthStatus.NEUTRAL
