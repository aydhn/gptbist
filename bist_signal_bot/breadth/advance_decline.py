import uuid
from datetime import datetime
from bist_signal_bot.breadth.models import AdvanceDeclineSummary, BreadthInputRow, BreadthScope, BreadthStatus
from bist_signal_bot.config.settings import Settings

class AdvanceDeclineCalculator:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def calculate(self, inputs: list[BreadthInputRow], scope: BreadthScope, scope_name: str) -> AdvanceDeclineSummary:
        if not inputs:
            return AdvanceDeclineSummary(
                summary_id=str(uuid.uuid4()),
                scope=scope,
                scope_name=scope_name,
                as_of=datetime.now(),
                advances=0,
                declines=0,
                unchanged=0,
                net_advances=0,
                status=BreadthStatus.INSUFFICIENT_DATA,
                warnings=["Empty inputs provided for AD calculation."]
            )

        advances = 0
        declines = 0
        unchanged = 0
        warnings = []

        # Take as_of from the first row or current time
        as_of = inputs[0].as_of if inputs else datetime.now()

        for row in inputs:
            if row.close is None or row.previous_close is None:
                warnings.append(f"Missing close data for {row.symbol}, skipping.")
                continue

            if row.close > row.previous_close:
                advances += 1
            elif row.close < row.previous_close:
                declines += 1
            else:
                unchanged += 1

        total_valid = advances + declines + unchanged
        if total_valid < self.settings.BREADTH_MIN_UNIVERSE_SIZE:
            warnings.append(f"Total valid symbols ({total_valid}) below minimum ({self.settings.BREADTH_MIN_UNIVERSE_SIZE}).")
            status = BreadthStatus.INSUFFICIENT_DATA
        else:
            # We don't classify status fully here, let scoring or regime handle it, or assign a basic one
            status = BreadthStatus.UNKNOWN

        summary = AdvanceDeclineSummary(
            summary_id=str(uuid.uuid4()),
            scope=scope,
            scope_name=scope_name,
            as_of=as_of,
            advances=advances,
            declines=declines,
            unchanged=unchanged,
            net_advances=self.net_advances(advances, declines),
            advance_decline_ratio=self.advance_decline_ratio(advances, declines),
            advance_percent=self.advance_percent(advances, declines, unchanged),
            status=status,
            warnings=warnings
        )
        summary.status = self.classify_summary(summary)
        return summary

    def classify_summary(self, summary: AdvanceDeclineSummary) -> BreadthStatus:
        if summary.status == BreadthStatus.INSUFFICIENT_DATA:
            return summary.status

        ratio = summary.advance_decline_ratio
        if ratio is None:
            return BreadthStatus.UNKNOWN

        if ratio >= 2.0:
            return BreadthStatus.STRONG
        elif ratio >= 1.2:
            return BreadthStatus.POSITIVE
        elif ratio <= 0.5:
            return BreadthStatus.WEAK
        elif ratio <= 0.8:
            return BreadthStatus.NEGATIVE
        return BreadthStatus.NEUTRAL

    def net_advances(self, advances: int, declines: int) -> int:
        return advances - declines

    def advance_decline_ratio(self, advances: int, declines: int) -> float | None:
        if declines == 0:
            return float(advances) if advances > 0 else 1.0 # Safe ratio
        return round(advances / declines, 4)

    def advance_percent(self, advances: int, declines: int, unchanged: int) -> float | None:
        total = advances + declines + unchanged
        if total == 0:
            return None
        return round((advances / total) * 100.0, 2)
