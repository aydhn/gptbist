import uuid
from datetime import datetime, timezone
from typing import Any
from bist_signal_bot.explainability.models import (
    ExplanationGovernanceAssessment,
    ExplanationObjectType,
    ExplanationStatus,
    FeatureAttribution,
    GlobalExplanation,
    ExplanationMethod
)

class ExplanationGovernanceEngine:
    def __init__(self, settings: Any = None):
        self.settings = settings
        self.unsafe_keywords = ["guarantee", "will cause", "sure", "trade ready", "live ready", "buy signal", "sell signal", "target price"]

    def assess_explainability(self, object_type: ExplanationObjectType, object_id: str) -> ExplanationGovernanceAssessment:
        return ExplanationGovernanceAssessment(
            assessment_id=str(uuid.uuid4()),
            object_type=object_type,
            object_id=object_id,
            created_at=datetime.now(timezone.utc),
            status=ExplanationStatus.UNKNOWN,
            explainability_available=True,
            method_supported=True
        )

    def feature_coverage_score(self, feature_names: list[str], available_explanations: list[FeatureAttribution]) -> float | None:
        if not feature_names:
            return None
        explained_features = set(a.feature_name for a in available_explanations)
        return (len(explained_features.intersection(feature_names)) / len(feature_names)) * 100.0

    def attribution_stability_score(self, explanations: list[GlobalExplanation]) -> float | None:
        # Mock calculation: 100.0 if consistent
        if not explanations:
            return None
        return 90.0

    def unsafe_language_findings(self, text: str) -> list[str]:
        findings = []
        lower_text = text.lower()
        for kw in self.unsafe_keywords:
            if kw in lower_text:
                findings.append(f"Unsafe claim detected: '{kw}'")
        return findings

    def caveats_for_method(self, method: ExplanationMethod) -> list[str]:
        caveats = []
        if method == ExplanationMethod.FEATURE_ATTRIBUTION:
            caveats.append("Feature attribution is not causal evidence.")
        elif method == ExplanationMethod.PERMUTATION_IMPORTANCE:
            caveats.append("Permutation importance assumes feature independence.")
        elif method == ExplanationMethod.COUNTERFACTUAL_RESEARCH:
            caveats.append("Counterfactuals are 'what-if' scenarios, not market forecasts.")
        return caveats

    def status_from_parts(self, method_supported: bool, coverage_score: float | None, unsafe_findings: list[str]) -> ExplanationStatus:
        if unsafe_findings:
            return ExplanationStatus.BLOCKED
        if not method_supported:
            return ExplanationStatus.UNSUPPORTED_MODEL
        if coverage_score is not None and coverage_score < 50.0:
            return ExplanationStatus.WATCH
        return ExplanationStatus.PASS
