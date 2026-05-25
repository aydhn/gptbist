import uuid
from typing import Any
from bist_signal_bot.explainability.models import (
    RuleTraceStep,
    StrategyRuleTrace,
    ExplanationStatus,
    ContributionDirection
)

class RuleTraceBuilder:
    def __init__(self, settings: Any = None):
        self.settings = settings

    def build_trace(
        self,
        strategy_name: str,
        symbol: str | None,
        feature_row: dict[str, Any],
        signal_payload: dict[str, Any] | None = None
    ) -> StrategyRuleTrace:
        steps = []
        if strategy_name == "moving_average_trend":
            steps = self.trace_moving_average_strategy(feature_row)
        elif strategy_name == "breakout":
            steps = self.trace_breakout_strategy(feature_row)
        elif strategy_name == "mean_reversion":
            steps = self.trace_mean_reversion_strategy(feature_row)
        else:
            steps = self.generic_trace(strategy_name, feature_row)

        passed_count = sum(1 for s in steps if s.passed)
        failed_count = sum(1 for s in steps if not s.passed)
        final_dir = ContributionDirection.SUPPORTS if passed_count > failed_count else ContributionDirection.OPPOSES
        status = ExplanationStatus.PASS if failed_count == 0 else ExplanationStatus.WARN

        return StrategyRuleTrace(
            trace_id=str(uuid.uuid4()),
            strategy_name=strategy_name,
            symbol=symbol,
            steps=steps,
            passed_count=passed_count,
            failed_count=failed_count,
            final_direction=final_dir,
            status=status
        )

    def trace_moving_average_strategy(self, row: dict[str, Any]) -> list[RuleTraceStep]:
        steps = []
        if "close" in row and "sma_50" in row:
            passed = row["close"] > row["sma_50"]
            steps.append(RuleTraceStep(
                step_id=str(uuid.uuid4()),
                rule_name="Price > SMA_50",
                condition="close > sma_50",
                observed_value=row["close"],
                expected_value=row["sma_50"],
                passed=passed,
                contribution_direction=ContributionDirection.SUPPORTS if passed else ContributionDirection.OPPOSES,
                message="Price is greater than 50-day moving average." if passed else "Price is lower than 50-day moving average."
            ))
        return steps

    def trace_breakout_strategy(self, row: dict[str, Any]) -> list[RuleTraceStep]:
        return []

    def trace_mean_reversion_strategy(self, row: dict[str, Any]) -> list[RuleTraceStep]:
        return []

    def generic_trace(self, strategy_name: str, row: dict[str, Any]) -> list[RuleTraceStep]:
        return [RuleTraceStep(
            step_id=str(uuid.uuid4()),
            rule_name="Generic condition",
            condition="unknown",
            observed_value=None,
            expected_value=None,
            passed=True,
            contribution_direction=ContributionDirection.NEUTRAL,
            message=f"Generic trace for {strategy_name}"
        )]
