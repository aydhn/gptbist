from copy import deepcopy
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.ml.inference.models import (
    MLInferenceConfig, MLInferenceResult, MLSignalFilterResult,
    MLFilterDecision, MLInferenceMode, MLFeatureAlignmentStatus, MLInferenceBatchResult
)
from bist_signal_bot.ml.inference.scoring import MLPredictionScorer
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection

class MLSignalFilter:
    def __init__(self, scorer: MLPredictionScorer | None = None, settings: Settings | None = None):
        self.scorer = scorer or MLPredictionScorer()
        self.settings = settings or Settings()

    def filter_signal(self, signal: SignalCandidate, inference_result: MLInferenceResult, config: MLInferenceConfig) -> MLSignalFilterResult:
        passed = True
        reject_reason = None
        warnings = list(inference_result.warnings)

        adjusted_score = signal.score
        adjusted_confidence = signal.confidence

        if config.mode == MLInferenceMode.DISABLED:
            decision = MLFilterDecision.SKIPPED
            passed = True
        else:
            decision = MLFilterDecision.PASS

            if config.mode in [MLInferenceMode.SCORE_ONLY, MLInferenceMode.SCORE_AND_FILTER]:
                adjusted_score, adjusted_confidence, blend_reasons = self.scorer.blend_signal_score(signal, inference_result.prediction_score, config)
                inference_result.reasons.extend(blend_reasons)

            if config.mode in [MLInferenceMode.FILTER_ONLY, MLInferenceMode.SCORE_AND_FILTER]:
                # Apply filter logic
                if inference_result.alignment.status == MLFeatureAlignmentStatus.FAILED:
                    decision = MLFilterDecision.REJECT
                    reject_reason = "Feature alignment failed."
                    passed = False
                elif inference_result.probability_positive is not None and inference_result.probability_positive < config.min_probability_positive:
                    decision = MLFilterDecision.REJECT
                    reject_reason = f"ML probability positive ({inference_result.probability_positive:.2f}) < min threshold ({config.min_probability_positive:.2f})"
                    passed = False
                elif inference_result.probability_negative is not None and inference_result.probability_negative > config.max_probability_negative:
                    decision = MLFilterDecision.REJECT
                    reject_reason = f"ML probability negative ({inference_result.probability_negative:.2f}) > max threshold ({config.max_probability_negative:.2f})"
                    passed = False
                elif inference_result.prediction_score < config.min_prediction_score:
                    decision = MLFilterDecision.REJECT
                    reject_reason = f"ML prediction score ({inference_result.prediction_score:.2f}) < min threshold ({config.min_prediction_score:.2f})"
                    passed = False

                # Trade direction validation
                if passed and signal.direction == SignalDirection.LONG:
                    if inference_result.probability_positive is not None and inference_result.probability_positive < 0.5:
                         warnings.append("ML model is negative on a LONG signal, but thresholds not breached.")

                if passed and signal.direction in [SignalDirection.FLAT, SignalDirection.WATCH]:
                    decision = MLFilterDecision.WATCH_ONLY

        inference_result.filter_decision = decision
        inference_result.original_signal_score = signal.score
        inference_result.adjusted_signal_score = adjusted_score
        inference_result.original_confidence = signal.confidence
        inference_result.adjusted_confidence = adjusted_confidence

        adjusted_signal = self.build_adjusted_signal(signal, adjusted_score, adjusted_confidence, inference_result)

        return MLSignalFilterResult(
            signal=signal,
            inference_result=inference_result,
            passed=passed,
            adjusted_signal=adjusted_signal,
            reject_reason=reject_reason,
            warnings=warnings
        )

    def build_adjusted_signal(self, signal: SignalCandidate, adjusted_score: float, adjusted_confidence: float, inference_result: MLInferenceResult) -> SignalCandidate:
        adj = deepcopy(signal)
        adj.score = adjusted_score
        adj.confidence = adjusted_confidence

        adj.metadata["ml_enabled"] = True
        adj.metadata["ml_model_id"] = inference_result.model_id
        adj.metadata["ml_prediction_score"] = inference_result.prediction_score
        adj.metadata["ml_prediction_direction"] = inference_result.prediction_direction.value
        adj.metadata["ml_probability_positive"] = inference_result.probability_positive
        adj.metadata["ml_filter_decision"] = inference_result.filter_decision.value
        adj.metadata["ml_adjusted_score"] = adjusted_score
        adj.metadata["ml_adjusted_confidence"] = adjusted_confidence
        adj.metadata["original_score"] = signal.score

        return adj

    def apply_to_batch(self, signals: list[SignalCandidate], inference_results: list[MLInferenceResult], config: MLInferenceConfig) -> MLInferenceBatchResult:
        # Assuming len(signals) == len(inference_results) mapped correctly beforehand
        pass_count = 0
        reject_count = 0
        err_count = 0
        filter_results = []

        for sig, inf in zip(signals, inference_results):
            if inf.filter_decision == MLFilterDecision.ERROR:
                err_count += 1
                continue

            res = self.filter_signal(sig, inf, config)
            filter_results.append(res)

            if res.passed:
                pass_count += 1
            else:
                reject_count += 1

        return MLInferenceBatchResult(
            results=inference_results,
            signal_filter_results=filter_results,
            requested_count=len(signals),
            passed_count=pass_count,
            rejected_count=reject_count,
            error_count=err_count,
            generated_at=inference_results[0].generated_at if inference_results else None,
            elapsed_seconds=sum([r.elapsed_seconds for r in inference_results])
        )
