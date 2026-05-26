import uuid
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.whatif.models import (
    WhatIfScenarioResult, SensitivityFinding, SensitivityDirection, AssumptionType
)

class SensitivityAnalyzer:
    def __init__(self, settings: Settings, logger: Any):
        self.settings = settings
        self.logger = logger
        self.metrics_to_track = [
            "portfolio_score",
            "diversification_score",
            "estimated_net_quality_score",
            "estimated_total_cost_bps",
            "estimated_turnover_pct",
            "constraint_violations_count",
            "max_drawdown_pct",
            "ruin_probability_pct"
        ]

    def analyze(self, baseline: WhatIfScenarioResult, scenarios: list[WhatIfScenarioResult]) -> list[SensitivityFinding]:
        findings = []
        for scenario in scenarios:
            for override in scenario.scenario.assumptions:
                for metric in self.metrics_to_track:
                    b_val = getattr(baseline, metric, None)
                    s_val = getattr(scenario, metric, None)
                    if b_val is not None and s_val is not None:
                        delta = self.metric_delta(metric, b_val, s_val)
                        if delta["delta_abs"] != 0:
                            direction = self.direction_for_metric(metric, delta["delta_pct"])
                            severity = self.severity_from_delta(metric, delta["delta_pct"])

                            findings.append(SensitivityFinding(
                                finding_id=str(uuid.uuid4()),
                                assumption_type=override.assumption_type,
                                metric_name=metric,
                                baseline_value=b_val,
                                scenario_value=s_val,
                                delta_abs=delta["delta_abs"],
                                delta_pct=delta["delta_pct"],
                                direction=direction,
                                severity=severity,
                                message=f"{metric} changed from {b_val} to {s_val} ({delta['delta_pct']:.2f}%).",
                                recommended_action=None
                            ))
        return findings

    def metric_delta(self, metric_name: str, baseline_value: float | None, scenario_value: float | None) -> dict[str, Any]:
        if baseline_value is None or scenario_value is None:
            return {"delta_abs": 0.0, "delta_pct": 0.0}

        delta_abs = scenario_value - baseline_value
        delta_pct = (delta_abs / abs(baseline_value) * 100.0) if baseline_value != 0 else 0.0
        return {"delta_abs": delta_abs, "delta_pct": delta_pct}

    def direction_for_metric(self, metric_name: str, delta_pct: float | None) -> SensitivityDirection:
        if delta_pct is None or delta_pct == 0:
            return SensitivityDirection.NEUTRAL

        inverse_metrics = [
            "estimated_total_cost_bps",
            "estimated_turnover_pct",
            "constraint_violations_count",
            "max_drawdown_pct",
            "ruin_probability_pct"
        ]

        if metric_name in inverse_metrics:
            if delta_pct > 0:
                return SensitivityDirection.WORSENS
            else:
                return SensitivityDirection.IMPROVES
        else:
            if delta_pct > 0:
                return SensitivityDirection.IMPROVES
            else:
                return SensitivityDirection.WORSENS

    def severity_from_delta(self, metric_name: str, delta_pct: float | None) -> str:
        if delta_pct is None:
            return "UNKNOWN"
        abs_delta = abs(delta_pct)
        warn_pct = getattr(self.settings, "WHATIF_SENSITIVITY_DELTA_WARN_PCT", 15.0)
        fail_pct = getattr(self.settings, "WHATIF_SENSITIVITY_DELTA_FAIL_PCT", 30.0)

        if abs_delta >= fail_pct:
            return "HIGH"
        elif abs_delta >= warn_pct:
            return "MEDIUM"
        else:
            return "LOW"
