import uuid
from typing import Any
from bist_signal_bot.explainability.models import (
    FeatureAttribution,
    ExplanationObjectType,
    ExplanationMethod,
    AttributionDirection
)

class ModelIntrospectionEngine:
    def __init__(self, settings: Any = None):
        self.settings = settings

    def introspect_model(self, model_like: Any, model_id: str = "unknown") -> dict[str, Any]:
        return {
            "model_id": model_id,
            "family": self.model_family(model_like),
            "supports_predict": self.supports_predict(model_like),
            "supports_feature_importance": self.supports_feature_importance(model_like),
            "summary": self.safe_model_summary(model_like)
        }

    def feature_names(self, model_like: Any) -> list[str]:
        if hasattr(model_like, "feature_names_in_"):
            return list(model_like.feature_names_in_)
        return []

    def native_feature_importance(self, model_like: Any) -> list[FeatureAttribution]:
        importances = []
        fnames = self.feature_names(model_like)

        if hasattr(model_like, "feature_importances_"):
            vals = model_like.feature_importances_
        elif hasattr(model_like, "coef_"):
            vals = model_like.coef_
            if hasattr(vals, "flatten"):
                vals = vals.flatten()
        else:
            return []

        for i, val in enumerate(vals):
            name = fnames[i] if i < len(fnames) else f"feature_{i}"
            score = float(val)
            direction = AttributionDirection.POSITIVE if score > 0 else (AttributionDirection.NEGATIVE if score < 0 else AttributionDirection.NEUTRAL)
            importances.append(FeatureAttribution(
                attribution_id=str(uuid.uuid4()),
                object_type=ExplanationObjectType.MODEL,
                object_id="unknown",
                feature_name=name,
                contribution_score=score,
                direction=direction,
                method=ExplanationMethod.MODEL_INTROSPECTION
            ))

        importances.sort(key=lambda a: abs(a.contribution_score or 0.0), reverse=True)
        return importances

    def model_family(self, model_like: Any) -> str:
        if type(model_like).__name__ == "dict":
            return "DictBaseline"
        if hasattr(model_like, "get_booster"):
            return "GradientBoosting"
        if hasattr(model_like, "coef_"):
            return "LinearModel"
        if hasattr(model_like, "feature_importances_"):
            return "TreeModel"
        if callable(model_like):
            return "CallableWrapper"
        return "Unknown"

    def supports_predict(self, model_like: Any) -> bool:
        return hasattr(model_like, "predict") or callable(model_like)

    def supports_feature_importance(self, model_like: Any) -> bool:
        return hasattr(model_like, "feature_importances_") or hasattr(model_like, "coef_")

    def safe_model_summary(self, model_like: Any) -> dict[str, Any]:
        return {
            "type_name": type(model_like).__name__,
            "is_callable": callable(model_like),
            "attributes_count": len(dir(model_like))
        }
