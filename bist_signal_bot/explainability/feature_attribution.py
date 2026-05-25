import uuid
from typing import Any
from bist_signal_bot.explainability.models import (
    FeatureContribution,
    ContributionDirection,
    ContributionStrength
)

class FeatureAttributionEngine:
    def __init__(self, settings: Any = None):
        self.settings = settings
        self.top_n = getattr(settings, "EXPLAINABILITY_TOP_FEATURES", 10) if settings else 10
        self.min_abs_score = getattr(settings, "EXPLAINABILITY_MIN_CONTRIBUTION_ABS_SCORE", 5.0) if settings else 5.0

    def attribute_features(
        self,
        features: dict[str, Any],
        signal_payload: dict[str, Any] | None = None,
        strategy_name: str | None = None
    ) -> list[FeatureContribution]:
        # A simple fallback feature attribution mock
        contributions = []
        for key, value in features.items():
            try:
                numeric_val = float(value)
            except (ValueError, TypeError):
                continue

            # Mock attribution based on feature magnitude
            score = numeric_val % 100.0 if numeric_val > 0 else (numeric_val % 100.0) - 100.0
            direction = self.direction_from_value(key, numeric_val, strategy_name)
            strength = self.strength_from_score(score)

            # Simple rule to skip weak features to keep list small
            if abs(score) < self.min_abs_score:
                continue

            contributions.append(
                FeatureContribution(
                    contribution_id=str(uuid.uuid4()),
                    feature_name=key,
                    value=numeric_val,
                    normalized_value=numeric_val,
                    contribution_score=score,
                    contribution_direction=direction,
                    strength=strength,
                    message=f"Feature {key} contributed with score {score:.2f}."
                )
            )

        return self.rank_contributions(contributions, self.top_n)

    def rank_contributions(self, contributions: list[FeatureContribution], top_n: int = 10) -> list[FeatureContribution]:
        return sorted(contributions, key=lambda c: abs(c.contribution_score or 0.0), reverse=True)[:top_n]

    def normalize_feature_value(self, feature_name: str, value: Any) -> float | None:
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def direction_from_value(self, feature_name: str, value: Any, strategy_name: str | None = None) -> ContributionDirection:
        val = self.normalize_feature_value(feature_name, value)
        if val is None:
            return ContributionDirection.UNKNOWN
        if val > 0:
            return ContributionDirection.SUPPORTS
        elif val < 0:
            return ContributionDirection.OPPOSES
        return ContributionDirection.NEUTRAL

    def strength_from_score(self, score: float | None) -> ContributionStrength:
        if score is None:
            return ContributionStrength.UNKNOWN
        abs_score = abs(score)
        if abs_score < 10.0:
            return ContributionStrength.VERY_WEAK
        elif abs_score < 30.0:
            return ContributionStrength.WEAK
        elif abs_score < 60.0:
            return ContributionStrength.MODERATE
        elif abs_score < 90.0:
            return ContributionStrength.STRONG
        return ContributionStrength.VERY_STRONG
