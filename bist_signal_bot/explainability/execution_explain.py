import uuid
from typing import Any
from bist_signal_bot.explainability.models import (
    ExecutionExplanation,
    FeatureContribution,
    ContributionDirection,
    ContributionStrength
)

class ExecutionExplainer:
    def __init__(self, settings: Any = None):
        self.settings = settings

    def explain_execution(self, fill_or_quality_payload: dict[str, Any]) -> ExecutionExplanation:
        factors = []
        liq = self.liquidity_contribution(fill_or_quality_payload)
        if liq: factors.append(liq)
        cost = self.cost_contribution(fill_or_quality_payload)
        if cost: factors.append(cost)
        slip = self.slippage_contribution(fill_or_quality_payload)
        if slip: factors.append(slip)
        fill = self.fill_probability_contribution(fill_or_quality_payload)
        if fill: factors.append(fill)

        return ExecutionExplanation(
            explanation_id=str(uuid.uuid4()),
            symbol=fill_or_quality_payload.get("symbol"),
            liquidity_status=fill_or_quality_payload.get("liquidity_status"),
            estimated_cost_bps=fill_or_quality_payload.get("cost_bps"),
            estimated_slippage_bps=fill_or_quality_payload.get("slippage_bps"),
            fill_probability=fill_or_quality_payload.get("fill_probability"),
            execution_factors=factors,
            warnings=[],
            disclaimer="Execution sim is research-only. Simulated fill does not guarantee real execution."
        )

    def liquidity_contribution(self, payload: dict[str, Any]) -> FeatureContribution | None:
        if "liquidity_status" in payload:
            return FeatureContribution(
                contribution_id=str(uuid.uuid4()),
                feature_name="Liquidity",
                contribution_direction=ContributionDirection.NEUTRAL,
                strength=ContributionStrength.MODERATE,
                message=f"Liquidity is {payload['liquidity_status']}"
            )
        return None

    def cost_contribution(self, payload: dict[str, Any]) -> FeatureContribution | None:
        if "cost_bps" in payload:
            return FeatureContribution(
                contribution_id=str(uuid.uuid4()),
                feature_name="Estimated Cost (bps)",
                value=payload["cost_bps"],
                contribution_direction=ContributionDirection.OPPOSES if payload["cost_bps"] > 10 else ContributionDirection.NEUTRAL,
                strength=ContributionStrength.MODERATE,
                message=f"Estimated cost: {payload['cost_bps']} bps."
            )
        return None

    def slippage_contribution(self, payload: dict[str, Any]) -> FeatureContribution | None:
        return None

    def fill_probability_contribution(self, payload: dict[str, Any]) -> FeatureContribution | None:
        return None
