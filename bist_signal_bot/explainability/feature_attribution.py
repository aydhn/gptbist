import uuid
from typing import Any
from bist_signal_bot.explainability.models import (
    FeatureAttribution,
    LocalExplanation,
    GlobalExplanation,
    ExplanationObjectType,
    ExplanationMethod,
    ExplanationScope,
    AttributionDirection,
    ExplanationStatus
)

class FeatureAttributionEngine:
    def __init__(self, settings: Any = None):
        self.settings = settings

    def explain_local(self, object_id: str, feature_row: dict[str, Any], prediction_value: float | None = None, baseline_value: float | None = None, object_type: ExplanationObjectType = ExplanationObjectType.MODEL) -> LocalExplanation:
        attributions = self.simple_attribution(feature_row, prediction_value, baseline_value, object_type, object_id)
        attributions = self.normalize_contributions(attributions)
        attributions = self.rank_attributions(attributions)

        return LocalExplanation(
            explanation_id=str(uuid.uuid4()),
            object_type=object_type,
            object_id=object_id,
            scope=ExplanationScope.LOCAL_ROW,
            method=ExplanationMethod.FEATURE_ATTRIBUTION,
            prediction_value=prediction_value,
            baseline_value=baseline_value,
            attributions=attributions,
            key_drivers=self.key_drivers(attributions),
            status=ExplanationStatus.PASS,
            warnings=["Deterministic fallback used." if not attributions else ""]
        )

    def explain_global(self, object_id: str, feature_rows: list[dict[str, Any]], object_type: ExplanationObjectType = ExplanationObjectType.MODEL) -> GlobalExplanation:
        if not feature_rows:
            return GlobalExplanation(
                explanation_id=str(uuid.uuid4()),
                object_type=object_type,
                object_id=object_id,
                scope=ExplanationScope.GLOBAL_MODEL,
                method=ExplanationMethod.FEATURE_ATTRIBUTION,
                status=ExplanationStatus.INSUFFICIENT_DATA,
                warnings=["No feature rows provided."]
            )

        agg_scores = {}
        for row in feature_rows:
            attrs = self.simple_attribution(row, object_type=object_type, object_id=object_id)
            for a in attrs:
                if a.contribution_score is not None:
                    agg_scores[a.feature_name] = agg_scores.get(a.feature_name, 0.0) + abs(a.contribution_score)

        global_attrs = []
        for fname, score in agg_scores.items():
            avg_score = score / len(feature_rows)
            global_attrs.append(FeatureAttribution(
                attribution_id=str(uuid.uuid4()),
                object_type=object_type,
                object_id=object_id,
                feature_name=fname,
                contribution_score=avg_score,
                direction=AttributionDirection.POSITIVE,
                method=ExplanationMethod.FEATURE_ATTRIBUTION
            ))

        global_attrs = self.normalize_contributions(global_attrs)
        global_attrs = self.rank_attributions(global_attrs)

        return GlobalExplanation(
            explanation_id=str(uuid.uuid4()),
            object_type=object_type,
            object_id=object_id,
            scope=ExplanationScope.GLOBAL_MODEL,
            method=ExplanationMethod.FEATURE_ATTRIBUTION,
            feature_importance=global_attrs,
            sample_count=len(feature_rows),
            top_features=self.key_drivers(global_attrs),
            status=ExplanationStatus.PASS
        )

    def simple_attribution(self, feature_row: dict[str, Any], prediction_value: float | None = None, baseline_value: float | None = None, object_type: ExplanationObjectType = ExplanationObjectType.MODEL, object_id: str = "unknown") -> list[FeatureAttribution]:
        contributions = []
        for key, value in feature_row.items():
            warnings = []
            try:
                numeric_val = float(value)
                score = numeric_val % 100.0 if numeric_val > 0 else (numeric_val % 100.0) - 100.0
                direction = AttributionDirection.POSITIVE if score > 0 else (AttributionDirection.NEGATIVE if score < 0 else AttributionDirection.NEUTRAL)
            except (ValueError, TypeError):
                numeric_val = None
                score = None
                direction = AttributionDirection.UNKNOWN
                warnings.append("Non-numeric feature excluded from contribution.")

            contributions.append(
                FeatureAttribution(
                    attribution_id=str(uuid.uuid4()),
                    object_type=object_type,
                    object_id=object_id,
                    feature_name=key,
                    feature_value=value,
                    contribution_score=score,
                    direction=direction,
                    method=ExplanationMethod.FALLBACK_SIMPLE,
                    warnings=warnings
                )
            )
        return contributions

    def normalize_contributions(self, attributions: list[FeatureAttribution]) -> list[FeatureAttribution]:
        total_abs = sum(abs(a.contribution_score) for a in attributions if a.contribution_score is not None)
        if total_abs == 0:
            return attributions

        for a in attributions:
            if a.contribution_score is not None:
                a.normalized_contribution = (a.contribution_score / total_abs) * 100.0
        return attributions

    def rank_attributions(self, attributions: list[FeatureAttribution]) -> list[FeatureAttribution]:
        ranked = sorted(attributions, key=lambda a: abs(a.contribution_score or 0.0), reverse=True)
        for i, a in enumerate(ranked):
            a.rank = i + 1
        return ranked

    def key_drivers(self, attributions: list[FeatureAttribution], limit: int = 5) -> list[str]:
        ranked = self.rank_attributions(attributions)
        return [a.feature_name for a in ranked[:limit] if a.contribution_score is not None]
