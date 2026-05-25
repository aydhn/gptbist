import uuid
from typing import Any
from bist_signal_bot.explainability.models import (
    EnsembleExplanation,
    FeatureContribution,
    ExplanationStatus,
    ContributionDirection,
    ContributionStrength
)

class EnsembleExplainer:
    def __init__(self, settings: Any = None):
        self.settings = settings

    def explain_consensus(self, consensus_payload: dict[str, Any]) -> EnsembleExplanation:
        components = self.component_contributions(consensus_payload)
        metrics = self.agreement_metrics(consensus_payload)

        agreement = metrics.get("agreement_count", 0)
        disagreement = metrics.get("disagreement_count", 0)
        conflict = metrics.get("conflict_score", 0.0)
        final_dir = ContributionDirection.SUPPORTS if agreement > disagreement else ContributionDirection.OPPOSES

        warnings = []
        if conflict > 0.5:
            warnings.append(self.conflict_message(conflict))

        return EnsembleExplanation(
            explanation_id=str(uuid.uuid4()),
            symbol=consensus_payload.get("symbol"),
            consensus_score=consensus_payload.get("score"),
            component_explanations=components,
            agreement_count=agreement,
            disagreement_count=disagreement,
            conflict_score=conflict,
            final_direction=final_dir,
            status=ExplanationStatus.PASS if conflict <= 0.5 else ExplanationStatus.WARN,
            warnings=warnings,
            disclaimer="Consensus logic is research-only and not investment advice. No real order was sent."
        )

    def component_contributions(self, consensus_payload: dict[str, Any]) -> list[FeatureContribution]:
        return []

    def agreement_metrics(self, consensus_payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "agreement_count": consensus_payload.get("agreement_count", 0),
            "disagreement_count": consensus_payload.get("disagreement_count", 0),
            "conflict_score": consensus_payload.get("conflict_score", 0.0)
        }

    def conflict_message(self, conflict_score: float | None) -> str:
        return f"High conflict among ensemble strategies (score: {conflict_score})."
