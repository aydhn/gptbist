import numpy as np
from typing import Any

from bist_signal_bot.stress.models import (
    ReturnSeries,
    DrawdownSimulationResult,
    StressStatus
)

class DrawdownSimulator:

    def analyze(self, series: ReturnSeries, initial_value: float = 100000.0) -> DrawdownSimulationResult:
        warnings = []
        status = StressStatus.PASS

        if not series.returns:
            warnings.append("Return series is empty.")
            return DrawdownSimulationResult(
                status=StressStatus.ERROR,
                warnings=warnings
            )

        equity_curve = self.equity_curve(series, initial_value)
        underwater = self.underwater_curve(equity_curve)

        max_dd = self.max_drawdown(underwater)
        avg_dd = self.average_drawdown(underwater)
        longest_dd = self.longest_drawdown_duration(underwater)
        recovery_days = self.estimate_recovery_days(underwater)

        return DrawdownSimulationResult(
            status=status,
            max_drawdown_pct=max_dd,
            average_drawdown_pct=avg_dd,
            longest_drawdown_days=longest_dd,
            recovery_days_estimate=recovery_days,
            underwater_curve=underwater,
            warnings=warnings
        )

    def equity_curve(self, series: ReturnSeries, initial_value: float) -> list[dict[str, Any]]:
        curve = []
        val = initial_value
        curve.append({"t": 0, "value": val, "return": 0.0})

        for i, r in enumerate(series.returns):
            val = val * (1 + r)
            curve.append({"t": i + 1, "value": val, "return": r})

        return curve

    def underwater_curve(self, equity_curve: list[dict[str, Any]]) -> list[dict[str, Any]]:
        underwater = []
        max_val = 0.0

        for pt in equity_curve:
            val = pt["value"]
            if val > max_val:
                max_val = val

            dd_pct = ((val - max_val) / max_val) * 100.0 if max_val > 0 else 0.0

            underwater.append({
                "t": pt["t"],
                "value": val,
                "peak": max_val,
                "drawdown_pct": dd_pct
            })

        return underwater

    def max_drawdown(self, underwater_curve: list[dict[str, Any]]) -> float | None:
        if not underwater_curve:
            return None
        return min(pt["drawdown_pct"] for pt in underwater_curve)

    def average_drawdown(self, underwater_curve: list[dict[str, Any]]) -> float | None:
        drawdowns = [pt["drawdown_pct"] for pt in underwater_curve if pt["drawdown_pct"] < 0]
        if not drawdowns:
            return 0.0
        return sum(drawdowns) / len(drawdowns)

    def longest_drawdown_duration(self, underwater_curve: list[dict[str, Any]]) -> int | None:
        if not underwater_curve:
            return None

        max_duration = 0
        current_duration = 0

        for pt in underwater_curve:
            if pt["drawdown_pct"] < 0:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0

        return max_duration

    def estimate_recovery_days(self, underwater_curve: list[dict[str, Any]]) -> int | None:
        # Simple heuristic: max drawdown duration is often roughly proportional to recovery
        longest = self.longest_drawdown_duration(underwater_curve)
        if longest is None:
            return None
        # Conservative estimate: recovery takes 1.5x to 2x the time of the fall
        return int(longest * 1.5)
