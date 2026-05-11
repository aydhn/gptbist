import pandas as pd
from typing import Any
from bist_signal_bot.ml.inference.models import MLInferenceResult, MLSignalFilterResult, MLInferenceBatchResult

def ml_inference_result_to_dict(result: MLInferenceResult) -> dict[str, Any]:
    return result.safe_public_dict()

def ml_signal_filter_result_to_dict(result: MLSignalFilterResult) -> dict[str, Any]:
    d = result.inference_result.safe_public_dict()
    d["passed"] = result.passed
    d["reject_reason"] = result.reject_reason
    return d

def ml_inference_batch_to_dataframe(batch: MLInferenceBatchResult) -> pd.DataFrame:
    rows = []
    if batch.signal_filter_results:
        for r in batch.signal_filter_results:
            d = ml_signal_filter_result_to_dict(r)
            rows.append(d)
    else:
        for r in batch.results:
            rows.append(ml_inference_result_to_dict(r))

    return pd.DataFrame(rows)

def format_ml_inference_text(result: MLInferenceResult) -> str:
    lines = [
        "ML Inference Research Output",
        f"Symbol: {result.symbol}",
        f"Model: {result.model_id}",
        f"Prediction Direction: {result.prediction_direction.value}",
        f"Score: {result.prediction_score:.2f}",
        f"Decision: {result.filter_decision.value}"
    ]
    if result.probability_positive is not None:
        lines.append(f"Positive Probability: {result.probability_positive:.2f}")
    if result.adjusted_signal_score is not None and result.original_signal_score is not None:
        lines.append(f"Original Score: {result.original_signal_score:.2f}")
        lines.append(f"Adjusted Score: {result.adjusted_signal_score:.2f}")
    if result.warnings:
        lines.append(f"Warnings: {len(result.warnings)}")

    lines.append("")
    lines.append("Disclaimer:")
    lines.append("This is an ML research output only. Not investment advice.")
    lines.append("No order was sent.")
    return "\n".join(lines)

def format_ml_signal_filter_text(result: MLSignalFilterResult) -> str:
    lines = [
        "ML Signal Filter Output",
        f"Symbol: {result.signal.symbol}",
        f"Model: {result.inference_result.model_id}",
        f"Passed: {'Yes' if result.passed else 'No'}",
        f"Decision: {result.inference_result.filter_decision.value}"
    ]
    if result.reject_reason:
        lines.append(f"Reason: {result.reject_reason}")
    if result.inference_result.probability_positive is not None:
        lines.append(f"Positive Probability: {result.inference_result.probability_positive:.2f}")

    lines.append(f"Original Score: {result.signal.score:.2f}")
    lines.append(f"Adjusted Score: {result.adjusted_signal.score:.2f}")

    lines.append("")
    lines.append("Disclaimer:")
    lines.append("This is an ML research filter only. Not investment advice.")
    lines.append("No order was sent.")
    return "\n".join(lines)

def format_ml_batch_text(batch: MLInferenceBatchResult) -> str:
    lines = [
        "ML Inference Batch Output",
        f"Requested: {batch.requested_count}",
        f"Passed: {batch.passed_count}",
        f"Rejected: {batch.rejected_count}",
        f"Errors: {batch.error_count}",
        f"Time: {batch.elapsed_seconds:.2f}s",
        "",
        "Disclaimer: ML research output only. Not investment advice. No real orders sent."
    ]
    return "\n".join(lines)
