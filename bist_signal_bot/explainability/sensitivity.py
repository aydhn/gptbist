import uuid
from typing import Any
from bist_signal_bot.explainability.models import (
    SensitivityAnalysisResult,
    SensitivityPoint,
    ExplanationObjectType,
    ExplanationStatus
)

class SensitivityAnalysisEngine:
    def __init__(self, settings: Any = None):
        self.settings = settings

    def analyze_feature(self, model_like: Any, feature_row: dict[str, Any], feature_name: str, perturbations: list[float] | None = None, object_id: str = "unknown") -> SensitivityAnalysisResult:
        original_value = feature_row.get(feature_name)
        warnings = []

        try:
            float(original_value)
        except (ValueError, TypeError):
            return SensitivityAnalysisResult(
                sensitivity_id=str(uuid.uuid4()),
                object_type=ExplanationObjectType.MODEL,
                object_id=object_id,
                feature_name=feature_name,
                points=[],
                status=ExplanationStatus.WATCH,
                warnings=["Non-numeric feature cannot be perturbed."]
            )

        if not perturbations:
            perturbations = self.default_perturbations(float(original_value))

        original_output = self.predict_one(model_like, feature_row)

        points = []
        for p in perturbations:
            perturbed_row = self.apply_perturbation(feature_row, feature_name, p)
            output = self.predict_one(model_like, perturbed_row)
            delta = output - original_output if (output is not None and original_output is not None) else None

            points.append(SensitivityPoint(
                point_id=str(uuid.uuid4()),
                feature_name=feature_name,
                original_value=float(original_value),
                perturbed_value=p,
                output_value=output,
                delta_output=delta
            ))

        return SensitivityAnalysisResult(
            sensitivity_id=str(uuid.uuid4()),
            object_type=ExplanationObjectType.MODEL,
            object_id=object_id,
            feature_name=feature_name,
            points=points,
            monotonicity_hint=self.monotonicity_hint(points),
            max_abs_delta=self.max_abs_delta(points),
            status=ExplanationStatus.PASS,
            warnings=warnings
        )

    def default_perturbations(self, value: float | None) -> list[float]:
        if value is None:
            value = 0.0
        if value == 0.0:
            return [-1.0, -0.5, 0.5, 1.0]
        return [value * 0.5, value * 0.8, value * 1.2, value * 1.5]

    def apply_perturbation(self, feature_row: dict[str, Any], feature_name: str, value: float) -> dict[str, Any]:
        row_copy = feature_row.copy()
        row_copy[feature_name] = value
        return row_copy

    def predict_one(self, model_like: Any, feature_row: dict[str, Any]) -> float | None:
        try:
            if hasattr(model_like, "predict"):
                preds = model_like.predict([feature_row])
                return float(preds[0])
            elif callable(model_like):
                return float(model_like(feature_row))
            return 0.0
        except Exception:
            return None

    def monotonicity_hint(self, points: list[SensitivityPoint]) -> str | None:
        if len(points) < 2:
            return None
        sorted_points = sorted(points, key=lambda p: p.perturbed_value or 0.0)
        increasing = all(sorted_points[i].output_value <= sorted_points[i+1].output_value for i in range(len(sorted_points)-1) if sorted_points[i].output_value is not None and sorted_points[i+1].output_value is not None)
        decreasing = all(sorted_points[i].output_value >= sorted_points[i+1].output_value for i in range(len(sorted_points)-1) if sorted_points[i].output_value is not None and sorted_points[i+1].output_value is not None)

        if increasing:
            return "Monotonically Increasing"
        if decreasing:
            return "Monotonically Decreasing"
        return "Non-Monotonic"

    def max_abs_delta(self, points: list[SensitivityPoint]) -> float | None:
        deltas = [abs(p.delta_output) for p in points if p.delta_output is not None]
        return max(deltas) if deltas else None
