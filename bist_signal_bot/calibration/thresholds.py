import uuid
from bist_signal_bot.calibration.models import (
    OutcomeRecord, CalibrationScoreType, OutcomeHorizon, ThresholdPolicy,
    ThresholdOptimizationResult, ThresholdPolicyStatus, CalibrationStatus, OutcomeLabel
)
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.calibration.metrics import CalibrationMetricsCalculator

class ThresholdTuner:
    def __init__(self, settings: Settings | None = None, metrics_calc: CalibrationMetricsCalculator | None = None):
        self.settings = settings or Settings()
        self.metrics_calc = metrics_calc or CalibrationMetricsCalculator(self.settings)

    def optimize_threshold(self, records: list[OutcomeRecord], score_type: CalibrationScoreType, horizon: OutcomeHorizon, objective: str = "net_return_quality") -> ThresholdOptimizationResult:
        candidates = self.candidate_thresholds()

        evaluations = []
        for thresh in candidates:
            eval_data = self.evaluate_threshold(records, score_type, thresh)
            eval_data['threshold'] = thresh
            evaluations.append(eval_data)

        selected_policy = self.select_threshold(evaluations, getattr(self.settings, "CALIBRATION_MIN_RECORDS", 50))

        policies = [self.policy_from_threshold(e['threshold'], e, score_type, horizon) for e in evaluations]

        if selected_policy:
            final_selected = self.policy_from_threshold(selected_policy['threshold'], selected_policy, score_type, horizon)
            if len(records) < getattr(self.settings, "CALIBRATION_MIN_RECORDS", 50):
                final_selected.status = ThresholdPolicyStatus.WATCH
                final_selected.warnings.append("Selected on small sample size.")
        else:
            final_selected = None

        strategy_name = records[0].strategy_name if records and all(r.strategy_name == records[0].strategy_name for r in records) else None

        return ThresholdOptimizationResult(
            optimization_id=str(uuid.uuid4()),
            score_type=score_type,
            strategy_name=strategy_name,
            horizon=horizon,
            candidate_thresholds=policies,
            selected_threshold=final_selected,
            objective_name=objective,
            sample_count=len(records),
            status=CalibrationStatus.PASS if final_selected else CalibrationStatus.WATCH
        )

    def evaluate_threshold(self, records: list[OutcomeRecord], score_type: CalibrationScoreType, threshold: float) -> dict[str, float | None]:
        total_evaluable = sum(1 for r in records if r.outcome_label != OutcomeLabel.NOT_EVALUATED)
        if total_evaluable == 0:
            return {"hit_rate": None, "signal_count": 0, "reduction_pct": 0.0, "net_return_quality": None}

        passed = [r for r in records if (getattr(r, 'confidence_score' if score_type.value.lower() == 'signal_confidence' else score_type.value.lower(), None) or 0) >= threshold and r.outcome_label != OutcomeLabel.NOT_EVALUATED]

        hit_rate = self.metrics_calc.hit_rate(passed)
        reduction_pct = 1.0 - (len(passed) / total_evaluable)

        net_returns = [r.net_return_pct for r in passed if r.net_return_pct is not None]
        avg_net = sum(net_returns) / len(net_returns) if net_returns else None

        quality = None
        if hit_rate is not None and avg_net is not None:
            quality = hit_rate * avg_net * (len(passed) ** 0.5)

        return {
            "hit_rate": hit_rate,
            "signal_count": len(passed),
            "reduction_pct": reduction_pct * 100.0,
            "net_return_quality": quality,
            "average_net_return": avg_net
        }

    def candidate_thresholds(self, start: float = 30.0, end: float = 90.0, step: float = 5.0) -> list[float]:
        s = getattr(self.settings, "CALIBRATION_THRESHOLD_START", start)
        e = getattr(self.settings, "CALIBRATION_THRESHOLD_END", end)
        st = getattr(self.settings, "CALIBRATION_THRESHOLD_STEP", step)

        current = s
        candidates = []
        while current <= e:
            candidates.append(current)
            current += st
        return candidates

    def select_threshold(self, evaluations: list[dict], min_samples: int) -> dict | None:
        valid_evals = [e for e in evaluations if e["signal_count"] >= min_samples and e["net_return_quality"] is not None]
        if not valid_evals:
            return None

        valid_evals.sort(key=lambda x: x["net_return_quality"], reverse=True)
        return valid_evals[0]

    def policy_from_threshold(self, threshold: float, evaluation: dict, score_type: CalibrationScoreType, horizon: OutcomeHorizon) -> ThresholdPolicy:
        return ThresholdPolicy(
            policy_id=str(uuid.uuid4()),
            score_type=score_type,
            threshold_value=threshold,
            horizon=horizon,
            reason=f"Optimized for net_return_quality. Hit rate: {evaluation.get('hit_rate')}, Avg Net: {evaluation.get('average_net_return')}",
            expected_signal_reduction_pct=evaluation.get("reduction_pct"),
            expected_quality_change={"net_return_quality": evaluation.get("net_return_quality")}
        )
