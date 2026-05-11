import os
import re

# Update backtesting/models.py
path = "bist_signal_bot/backtesting/models.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()
    if "use_ml_filter: bool = Field(default=False)" not in content:
        content = content.replace("enable_telemetry: bool = Field(default=False)", "enable_telemetry: bool = Field(default=False)\n    use_ml_filter: bool = Field(default=False)\n    ml_model_id: str | None = Field(default=None)")
        with open(path, "w") as f:
            f.write(content)

# Update risk/filters.py
path = "bist_signal_bot/risk/filters.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    ml_filter_cls = """
class MLScoreFilter(RiskFilter):
    def evaluate(self, candidate: SignalCandidate) -> FilterResult:
        use_ml = getattr(self.settings, "RISK_USE_ML_FILTER", False)
        if not use_ml:
            return FilterResult(passed=True)

        reject_missing = getattr(self.settings, "RISK_REJECT_IF_ML_MISSING", False)

        if "ml_prediction_score" not in candidate.metadata:
            if reject_missing:
                return FilterResult(passed=False, reason="ML score missing but required by risk filter")
            return FilterResult(passed=True, reason="ML score missing, but not strictly required")

        score = candidate.metadata["ml_prediction_score"]
        prob = candidate.metadata.get("ml_probability_positive")
        min_score = getattr(self.settings, "RISK_MIN_ML_SCORE", 50.0)
        min_prob = getattr(self.settings, "RISK_MIN_ML_PROBABILITY_POSITIVE", 0.55)

        if score < min_score:
            return FilterResult(passed=False, reason=f"ML Score {score} < {min_score}")
        if prob is not None and prob < min_prob:
            return FilterResult(passed=False, reason=f"ML Probability {prob} < {min_prob}")

        return FilterResult(passed=True, reason="ML Risk Filter Passed")
"""
    if "MLScoreFilter" not in content:
        content = content + ml_filter_cls
        with open(path, "w") as f:
            f.write(content)

print("Updated backtesting models and risk filters")
