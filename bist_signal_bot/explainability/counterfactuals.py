import uuid
from typing import Any
from bist_signal_bot.explainability.models import (
    CounterfactualScenario,
    ExplanationObjectType,
    ExplanationStatus
)

class CounterfactualResearchEngine:
    def __init__(self, settings: Any = None):
        self.settings = settings

    def generate_counterfactual(self, model_like: Any, feature_row: dict[str, Any], changed_features: dict[str, Any], object_id: str = "unknown", symbol: str | None = None) -> CounterfactualScenario:
        original_output = self.predict(model_like, feature_row)

        counterfactual_row = feature_row.copy()
        counterfactual_row.update(changed_features)

        counterfactual_output = self.predict(model_like, counterfactual_row)
        delta = counterfactual_output - original_output if (original_output is not None and counterfactual_output is not None) else None

        status = self.plausibility_check(feature_row, changed_features)
        warnings = []
        if status == ExplanationStatus.WATCH:
            warnings.append("Implausible counterfactual values detected.")

        return CounterfactualScenario(
            counterfactual_id=str(uuid.uuid4()),
            object_type=ExplanationObjectType.MODEL,
            object_id=object_id,
            symbol=symbol,
            changed_features=changed_features,
            original_output=original_output,
            counterfactual_output=counterfactual_output,
            delta_output=delta,
            plausibility_status=status,
            warnings=warnings
        )

    def predict(self, model_like: Any, feature_row: dict[str, Any]) -> float | None:
        try:
            if hasattr(model_like, "predict"):
                preds = model_like.predict([feature_row])
                return float(preds[0])
            elif callable(model_like):
                return float(model_like(feature_row))
            return 0.0
        except Exception:
            return None

    def plausibility_check(self, feature_row: dict[str, Any], changed_features: dict[str, Any]) -> ExplanationStatus:
        for k, v in changed_features.items():
            orig = feature_row.get(k)
            try:
                orig_val = float(orig)
                new_val = float(v)
                # Mark as implausible if change is > 5x magnitude
                if orig_val != 0 and abs(new_val / orig_val) > 5.0:
                    return ExplanationStatus.WATCH
            except (ValueError, TypeError):
                return ExplanationStatus.WATCH
        return ExplanationStatus.PASS

    def generate_feature_grid_counterfactuals(self, model_like: Any, feature_row: dict[str, Any], feature_name: str, values: list[Any], object_id: str = "unknown") -> list[CounterfactualScenario]:
        scenarios = []
        for val in values:
            scenarios.append(self.generate_counterfactual(model_like, feature_row, {feature_name: val}, object_id=object_id))
        return scenarios

    def counterfactual_summary(self, counterfactuals: list[CounterfactualScenario]) -> list[str]:
        summary = []
        for cf in counterfactuals:
            if cf.delta_output is not None:
                summary.append(f"Scenario {cf.counterfactual_id}: output delta {cf.delta_output:.4f}")
        return summary
