import uuid
from datetime import datetime
from bist_signal_bot.breadth.models import BreadthInputRow, BreadthScope, BreadthStatus, VolumeBreadthSummary
from bist_signal_bot.config.settings import Settings

class VolumeBreadthAnalyzer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def analyze(self, inputs: list[BreadthInputRow], scope: BreadthScope, scope_name: str) -> VolumeBreadthSummary:
        if not inputs:
            return VolumeBreadthSummary(
                volume_breadth_id=str(uuid.uuid4()),
                scope=scope,
                scope_name=scope_name,
                as_of=datetime.now(),
                status=BreadthStatus.INSUFFICIENT_DATA,
                warnings=["Empty inputs provided for volume breadth calculation."]
            )

        as_of = inputs[0].as_of if inputs else datetime.now()

        up_down = self.up_down_volume(inputs)
        up_vol = up_down.get("up", 0.0)
        down_vol = up_down.get("down", 0.0)
        unchanged_vol = up_down.get("unchanged", 0.0)

        ratios = self.volume_ratio(up_vol, down_vol)

        summary = VolumeBreadthSummary(
            volume_breadth_id=str(uuid.uuid4()),
            scope=scope,
            scope_name=scope_name,
            as_of=as_of,
            up_volume=up_vol,
            down_volume=down_vol,
            unchanged_volume=unchanged_vol,
            up_volume_ratio=ratios.get("up_ratio"),
            down_volume_ratio=ratios.get("down_ratio")
        )

        summary.volume_breadth_score = self.volume_breadth_score(summary)
        summary.status = self.classify_volume_breadth(summary.volume_breadth_score)

        return summary

    def up_down_volume(self, inputs: list[BreadthInputRow]) -> dict[str, float]:
        up = 0.0
        down = 0.0
        unchanged = 0.0

        for row in inputs:
            if row.volume is None or row.close is None or row.previous_close is None:
                continue

            if row.close > row.previous_close:
                up += row.volume
            elif row.close < row.previous_close:
                down += row.volume
            else:
                unchanged += row.volume

        return {"up": up, "down": down, "unchanged": unchanged}

    def volume_ratio(self, up_volume: float | None, down_volume: float | None) -> dict[str, float | None]:
        up = up_volume or 0.0
        down = down_volume or 0.0
        total = up + down

        if total == 0:
            return {"up_ratio": None, "down_ratio": None}

        return {
            "up_ratio": round((up / total) * 100.0, 2),
            "down_ratio": round((down / total) * 100.0, 2)
        }

    def volume_breadth_score(self, summary: VolumeBreadthSummary) -> float | None:
        return summary.up_volume_ratio

    def classify_volume_breadth(self, score: float | None) -> BreadthStatus:
        if score is None:
            return BreadthStatus.UNKNOWN
        if score >= 70.0:
            return BreadthStatus.STRONG
        elif score >= 55.0:
            return BreadthStatus.POSITIVE
        elif score <= 30.0:
            return BreadthStatus.WEAK
        elif score <= 45.0:
            return BreadthStatus.NEGATIVE
        return BreadthStatus.NEUTRAL
