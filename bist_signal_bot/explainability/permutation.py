import uuid
import random
from typing import Any
from bist_signal_bot.explainability.models import (
    GlobalExplanation,
    FeatureAttribution,
    ExplanationObjectType,
    ExplanationMethod,
    ExplanationScope,
    ExplanationStatus,
    AttributionDirection
)

class PermutationImportanceEngine:
    def __init__(self, settings: Any = None):
        self.settings = settings
        self.default_seed = getattr(settings, "EXPLAINABILITY_DEFAULT_SEED", 42) if settings else 42

    def compute_importance(self, model_like: Any, feature_rows: list[dict[str, Any]], target_values: list[float] | None = None, feature_names: list[str] | None = None, seed: int = 42) -> GlobalExplanation:
        if not feature_rows or len(feature_rows) < 2:
            return GlobalExplanation(
                explanation_id=str(uuid.uuid4()),
                object_type=ExplanationObjectType.MODEL,
                object_id="unknown",
                scope=ExplanationScope.GLOBAL_MODEL,
                method=ExplanationMethod.PERMUTATION_IMPORTANCE,
                status=ExplanationStatus.INSUFFICIENT_DATA,
                warnings=["Insufficient data for permutation importance (needs >= 2)."]
            )

        if not hasattr(model_like, "predict") and not callable(model_like):
            return GlobalExplanation(
                explanation_id=str(uuid.uuid4()),
                object_type=ExplanationObjectType.MODEL,
                object_id="unknown",
                scope=ExplanationScope.GLOBAL_MODEL,
                method=ExplanationMethod.PERMUTATION_IMPORTANCE,
                status=ExplanationStatus.UNSUPPORTED_MODEL,
                warnings=["Model lacks predict method; fallback used."]
            )

        if not feature_names:
            feature_names = list(feature_rows[0].keys())

        baseline_preds = self.predict_with_model(model_like, feature_rows)
        baseline_score = self.score_predictions(baseline_preds, target_values)

        importances = []
        for fname in feature_names:
            permuted_rows = self.permute_feature(feature_rows, fname, seed)
            permuted_preds = self.predict_with_model(model_like, permuted_rows)
            permuted_score = self.score_predictions(permuted_preds, target_values)

            importances.append(self.importance_from_score_delta(fname, baseline_score, permuted_score))

        # rank
        importances.sort(key=lambda a: abs(a.contribution_score or 0.0), reverse=True)
        for i, a in enumerate(importances):
            a.rank = i + 1

        top_features = [a.feature_name for a in importances[:5]]

        return GlobalExplanation(
            explanation_id=str(uuid.uuid4()),
            object_type=ExplanationObjectType.MODEL,
            object_id="unknown",
            scope=ExplanationScope.GLOBAL_MODEL,
            method=ExplanationMethod.PERMUTATION_IMPORTANCE,
            feature_importance=importances,
            sample_count=len(feature_rows),
            top_features=top_features,
            status=ExplanationStatus.PASS
        )

    def permute_feature(self, rows: list[dict[str, Any]], feature_name: str, seed: int = 42) -> list[dict[str, Any]]:
        rng = random.Random(seed)
        values = [r.get(feature_name) for r in rows]
        rng.shuffle(values)

        new_rows = [r.copy() for r in rows]
        for i, r in enumerate(new_rows):
            r[feature_name] = values[i]
        return new_rows

    def score_predictions(self, predictions: list[float], target_values: list[float] | None = None) -> float | None:
        if not predictions:
            return None
        if target_values and len(target_values) == len(predictions):
            diffs = [(p - t)**2 for p, t in zip(predictions, target_values)]
            return -sum(diffs) / len(diffs)
        mean = sum(predictions) / len(predictions)
        return sum((p - mean)**2 for p in predictions) / len(predictions)

    def predict_with_model(self, model_like: Any, rows: list[dict[str, Any]]) -> list[float]:
        try:
            if hasattr(model_like, "predict"):
                return list(model_like.predict(rows))
            elif callable(model_like):
                return [float(model_like(r)) for r in rows]
            return [0.0] * len(rows)
        except Exception:
            return [0.0] * len(rows)

    def importance_from_score_delta(self, feature_name: str, baseline_score: float | None, permuted_score: float | None) -> FeatureAttribution:
        if baseline_score is None or permuted_score is None:
            score = 0.0
        else:
            score = baseline_score - permuted_score

        direction = AttributionDirection.POSITIVE if score > 0 else (AttributionDirection.NEGATIVE if score < 0 else AttributionDirection.NEUTRAL)
        return FeatureAttribution(
            attribution_id=str(uuid.uuid4()),
            object_type=ExplanationObjectType.MODEL,
            object_id="unknown",
            feature_name=feature_name,
            contribution_score=score,
            direction=direction,
            method=ExplanationMethod.PERMUTATION_IMPORTANCE
        )
