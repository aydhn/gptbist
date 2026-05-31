import uuid
from datetime import datetime
from bist_signal_bot.monitoring.models import MonitoringObjectType, ChampionChallengerComparison, ChampionChallengerDecision, MonitoringMetric

class ChampionChallengerEngine:
    def __init__(self, min_sample: int = 50, promotion_margin: float = 5.0):
        self.min_sample = min_sample
        self.promotion_margin = promotion_margin

    def compare(self, object_type: MonitoringObjectType, champion_id: str, challenger_id: str, as_of: datetime | None = None) -> ChampionChallengerComparison:
        as_of = as_of or datetime.now()

        # In a real implementation, we'd fetch actual metrics.
        # Mocking empty metrics for the skeleton.
        champ_metrics = []
        chall_metrics = []

        sample_warnings = self.minimum_sample_check(champ_metrics, chall_metrics)
        if sample_warnings:
            decision = ChampionChallengerDecision.NEEDS_MORE_DATA
            score = None
            reasons = sample_warnings
        else:
            decision = self.decision_from_metrics(champ_metrics, chall_metrics)
            score = self.decision_score(champ_metrics, chall_metrics)
            reasons = self.comparison_reasons(champ_metrics, chall_metrics)

        return ChampionChallengerComparison(
            comparison_id=str(uuid.uuid4()),
            object_type=object_type,
            champion_id=champion_id,
            challenger_id=challenger_id,
            as_of=as_of,
            champion_metrics=champ_metrics,
            challenger_metrics=chall_metrics,
            decision=decision,
            decision_score=score,
            reasons=reasons,
            warnings=sample_warnings
        )

    def decision_from_metrics(self, champion: list[MonitoringMetric], challenger: list[MonitoringMetric]) -> ChampionChallengerDecision:
        if not champion or not challenger:
            return ChampionChallengerDecision.NEEDS_MORE_DATA

        score = self.decision_score(champion, challenger)
        if score is None:
            return ChampionChallengerDecision.NEEDS_MORE_DATA

        if score > self.promotion_margin:
            return ChampionChallengerDecision.PROMOTE_CHALLENGER_RESEARCH
        elif score < -self.promotion_margin:
            return ChampionChallengerDecision.REJECT_CHALLENGER

        return ChampionChallengerDecision.KEEP_CHAMPION

    def decision_score(self, champion: list[MonitoringMetric], challenger: list[MonitoringMetric]) -> float | None:
        # Score calculation. E.g., difference in average expectancy * 100
        champ_exp = next((m.value for m in champion if m.metric_name == 'expectancy' and m.value is not None), None)
        chall_exp = next((m.value for m in challenger if m.metric_name == 'expectancy' and m.value is not None), None)

        if champ_exp is None or chall_exp is None:
            return None

        # If expectancy is 0 for champion, avoid division by zero.
        if champ_exp == 0:
            return chall_exp * 100.0 if chall_exp > 0 else 0.0

        return ((chall_exp - champ_exp) / abs(champ_exp)) * 100.0

    def comparison_reasons(self, champion: list[MonitoringMetric], challenger: list[MonitoringMetric]) -> list[str]:
        score = self.decision_score(champion, challenger)
        if score is None:
            return ["Cannot compute score due to missing metrics."]

        if score > self.promotion_margin:
            return [f"Challenger outperformed champion by {score:.2f}% (Margin: {self.promotion_margin}%)"]
        elif score < -self.promotion_margin:
            return [f"Champion outperformed challenger by {abs(score):.2f}%"]

        return [f"Performance difference ({score:.2f}%) within margin ({self.promotion_margin}%)."]

    def minimum_sample_check(self, champion: list[MonitoringMetric], challenger: list[MonitoringMetric]) -> list[str]:
        warnings = []
        champ_samples = next((m.sample_count for m in champion if m.sample_count is not None), 0)
        chall_samples = next((m.sample_count for m in challenger if m.sample_count is not None), 0)

        if champ_samples < self.min_sample:
            warnings.append(f"Champion sample size ({champ_samples}) below minimum ({self.min_sample}).")
        if chall_samples < self.min_sample:
            warnings.append(f"Challenger sample size ({chall_samples}) below minimum ({self.min_sample}).")

        return warnings
