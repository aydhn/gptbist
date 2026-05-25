import uuid
from typing import Any
from bist_signal_bot.explainability.models import (
    IndicatorExplanation,
    ContributionDirection,
    ContributionStrength
)

class IndicatorStateExplainer:
    def __init__(self, settings: Any = None):
        self.settings = settings

    def explain_indicators(self, feature_row: dict[str, Any], strategy_name: str | None = None) -> list[IndicatorExplanation]:
        explanations = []
        explanations.extend(self.explain_moving_average_state(feature_row))
        explanations.extend(self.explain_rsi_state(feature_row))
        explanations.extend(self.explain_macd_state(feature_row))
        explanations.extend(self.explain_volume_state(feature_row))
        explanations.extend(self.explain_volatility_state(feature_row))
        return explanations

    def explain_moving_average_state(self, row: dict[str, Any]) -> list[IndicatorExplanation]:
        explanations = []
        # Mock logic
        if "sma_50" in row and "close" in row:
            val = row["sma_50"]
            close = row["close"]
            direction = ContributionDirection.SUPPORTS if close > val else ContributionDirection.OPPOSES
            explanations.append(
                IndicatorExplanation(
                    indicator_id=str(uuid.uuid4()),
                    indicator_name="SMA_50",
                    value=val,
                    threshold=close,
                    state="Above SMA" if close > val else "Below SMA",
                    contribution_direction=direction,
                    strength=ContributionStrength.MODERATE,
                    message="Price is above 50-day SMA, indicating upward trend." if close > val else "Price is below 50-day SMA, indicating downward trend."
                )
            )
        return explanations

    def explain_rsi_state(self, row: dict[str, Any]) -> list[IndicatorExplanation]:
        explanations = []
        if "rsi_14" in row:
            val = row["rsi_14"]
            direction = ContributionDirection.SUPPORTS if val < 30 else (ContributionDirection.OPPOSES if val > 70 else ContributionDirection.NEUTRAL)
            state = "Oversold" if val < 30 else ("Overbought" if val > 70 else "Neutral")
            explanations.append(
                IndicatorExplanation(
                    indicator_id=str(uuid.uuid4()),
                    indicator_name="RSI_14",
                    value=val,
                    threshold=None,
                    state=state,
                    contribution_direction=direction,
                    strength=ContributionStrength.MODERATE,
                    message=f"RSI is {val:.2f} ({state})."
                )
            )
        return explanations

    def explain_macd_state(self, row: dict[str, Any]) -> list[IndicatorExplanation]:
        return []

    def explain_volume_state(self, row: dict[str, Any]) -> list[IndicatorExplanation]:
        return []

    def explain_volatility_state(self, row: dict[str, Any]) -> list[IndicatorExplanation]:
        return []
