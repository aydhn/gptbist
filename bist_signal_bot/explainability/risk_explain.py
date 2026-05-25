import uuid
from typing import Any
from bist_signal_bot.explainability.models import (
    RiskExplanation,
    FeatureContribution
)

class RiskExplainer:
    def __init__(self, settings: Any = None):
        self.settings = settings

    def explain_risk(self, risk_payload: dict[str, Any]) -> RiskExplanation:
        factors = self.risk_factor_contributions(risk_payload)
        reasons = self.blocking_reasons(risk_payload)

        return RiskExplanation(
            explanation_id=str(uuid.uuid4()),
            symbol=risk_payload.get("symbol"),
            risk_status=risk_payload.get("status", "UNKNOWN"),
            risk_score=risk_payload.get("score"),
            risk_factors=factors,
            blocking_reasons=reasons,
            warnings=[],
            disclaimer="Risk explanation is research-only. Position sizing rules are theoretical and no real order was sent."
        )

    def risk_factor_contributions(self, risk_payload: dict[str, Any]) -> list[FeatureContribution]:
        return []

    def blocking_reasons(self, risk_payload: dict[str, Any]) -> list[str]:
        return risk_payload.get("blocking_reasons", [])
