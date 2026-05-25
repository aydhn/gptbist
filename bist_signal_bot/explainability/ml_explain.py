import uuid
from typing import Any
from bist_signal_bot.explainability.models import (
    MLExplanation,
    FeatureContribution,
    ExplanationStatus,
    ContributionDirection,
    ContributionStrength
)

class MLExplainer:
    def __init__(self, settings: Any = None):
        self.settings = settings
        self.use_model_importance = getattr(settings, "EXPLAINABILITY_USE_MODEL_IMPORTANCE_IF_AVAILABLE", True) if settings else True
        self.use_permutation = getattr(settings, "EXPLAINABILITY_USE_PERMUTATION_FALLBACK", False) if settings else False

    def explain_prediction(self, model: Any, feature_row: dict[str, Any], model_name: str | None = None, symbol: str | None = None) -> MLExplanation:
        top_features = []
        method = "fallback"
        status = ExplanationStatus.PASS
        warnings = []

        try:
            if self.use_model_importance and hasattr(model, "feature_importances_"):
                # Mock logic for feature importances
                importances = self.feature_importance_from_model(model, list(feature_row.keys()))
                method = "feature_importances"
                for f, score in importances.items():
                    top_features.append(
                        FeatureContribution(
                            contribution_id=str(uuid.uuid4()),
                            feature_name=f,
                            value=feature_row.get(f),
                            normalized_value=feature_row.get(f) if isinstance(feature_row.get(f), (int, float)) else None,
                            contribution_score=score * 100,
                            contribution_direction=ContributionDirection.SUPPORTS if score > 0 else ContributionDirection.OPPOSES,
                            strength=ContributionStrength.MODERATE,
                            message=f"Feature {f} importance: {score:.4f}"
                        )
                    )
            elif self.use_permutation:
                top_features = self.permutation_like_local_importance(model, feature_row)
                method = "permutation"
            else:
                top_features = self.fallback_feature_explanation(feature_row)
                method = "fallback"
        except Exception as e:
            status = ExplanationStatus.WARN
            warnings.append(f"Model explanation failed: {str(e)}")
            top_features = self.fallback_feature_explanation(feature_row)

        return MLExplanation(
            explanation_id=str(uuid.uuid4()),
            model_name=model_name,
            symbol=symbol,
            predicted_score=None,
            top_features=top_features[:10],
            method=method,
            status=status,
            warnings=warnings
        )

    def feature_importance_from_model(self, model: Any, feature_names: list[str]) -> dict[str, float]:
        importances = getattr(model, "feature_importances_", [])
        return {f: float(i) for f, i in zip(feature_names, importances)}

    def permutation_like_local_importance(self, model: Any, feature_row: dict[str, Any]) -> list[FeatureContribution]:
        return self.fallback_feature_explanation(feature_row)

    def fallback_feature_explanation(self, feature_row: dict[str, Any]) -> list[FeatureContribution]:
        return []
