import pandas as pd
from typing import Any
from bist_signal_bot.ml.training.models import MLTrainResult, MLPredictionResult, MLFeatureImportance

def ml_train_result_to_dict(result: MLTrainResult) -> dict[str, Any]:
    return result.summary()

def ml_prediction_result_to_dict(result: MLPredictionResult) -> dict[str, Any]:
    return result.summary()

def feature_importance_to_dataframe(items: list[MLFeatureImportance]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame()
    df = pd.DataFrame([f.model_dump() for f in items])
    return df

def format_ml_train_text(result: MLTrainResult) -> str:
    lines = [
        "=== ML Training Summary ===",
        f"Status: {result.status.value}",
        f"Model: {result.config.model_type.value}",
        f"Task: {result.config.task_type.value}",
        f"Target: {result.config.target_col}",
        f"Train Rows: {result.prepared_data_summary.get('train_rows', 0)}",
        f"Test Rows: {result.prepared_data_summary.get('test_rows', 0)}",
    ]

    if result.artifact and result.artifact.model_id:
        lines.append(f"Model ID: {result.artifact.model_id}")

    lines.append("\n-- Metrics --")
    if result.classification_metrics:
        m = result.classification_metrics
        lines.append(f"Accuracy: {m.accuracy:.4f}" if m.accuracy is not None else "Accuracy: N/A")
        lines.append(f"F1 Score: {m.f1:.4f}" if m.f1 is not None else "F1 Score: N/A")
        lines.append(f"ROC AUC: {m.roc_auc:.4f}" if m.roc_auc is not None else "ROC AUC: N/A")
    elif result.regression_metrics:
        m = result.regression_metrics
        lines.append(f"MAE: {m.mae:.4f}" if m.mae is not None else "MAE: N/A")
        lines.append(f"RMSE: {m.rmse:.4f}" if m.rmse is not None else "RMSE: N/A")
        lines.append(f"R2 Score: {m.r2:.4f}" if m.r2 is not None else "R2 Score: N/A")

    if result.feature_importance:
        lines.append("\n-- Top 5 Features --")
        for i, fi in enumerate(result.feature_importance[:5]):
            lines.append(f"{i+1}. {fi.feature} ({fi.importance:.4f})")

    if result.issues:
        lines.append("\n-- Issues --")
        for issue in result.issues:
            lines.append(f"  - {issue}")

    lines.append("\nDisclaimer: " + result.disclaimer)
    return "\n".join(lines)

def format_ml_train_markdown(result: MLTrainResult) -> str:
    lines = [
        "# ML Training Report",
        f"**Status:** {result.status.value}",
        f"**Model:** {result.config.model_type.value}",
        f"**Task:** {result.config.task_type.value}",
        f"**Target:** `{result.config.target_col}`",
        f"**Train/Test Rows:** {result.prepared_data_summary.get('train_rows', 0)} / {result.prepared_data_summary.get('test_rows', 0)}",
    ]

    if result.artifact and result.artifact.model_id:
        lines.append(f"**Model ID:** `{result.artifact.model_id}`")

    lines.append("\n## Metrics")
    if result.classification_metrics:
        m = result.classification_metrics
        lines.append(f"- **Accuracy:** {m.accuracy:.4f}" if m.accuracy is not None else "- **Accuracy:** N/A")
        lines.append(f"- **F1 Score:** {m.f1:.4f}" if m.f1 is not None else "- **F1 Score:** N/A")
        lines.append(f"- **ROC AUC:** {m.roc_auc:.4f}" if m.roc_auc is not None else "- **ROC AUC:** N/A")
    elif result.regression_metrics:
        m = result.regression_metrics
        lines.append(f"- **MAE:** {m.mae:.4f}" if m.mae is not None else "- **MAE:** N/A")
        lines.append(f"- **RMSE:** {m.rmse:.4f}" if m.rmse is not None else "- **RMSE:** N/A")
        lines.append(f"- **R2 Score:** {m.r2:.4f}" if m.r2 is not None else "- **R2 Score:** N/A")

    if result.feature_importance:
        lines.append("\n## Top 10 Features")
        for i, fi in enumerate(result.feature_importance[:10]):
            lines.append(f"{i+1}. `{fi.feature}` ({fi.importance:.4f})")

    if result.issues:
        lines.append("\n## Issues")
        for issue in result.issues:
            lines.append(f"- {issue}")

    lines.append("\n---\n*Disclaimer: " + result.disclaimer + "*")
    return "\n".join(lines)

def format_ml_prediction_text(result: MLPredictionResult) -> str:
    lines = [
        "=== ML Prediction Summary ===",
        f"Model ID: {result.model_id}",
        f"Total Predictions: {result.row_count}",
        f"Generated At: {result.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
    ]

    if result.predictions:
        lines.append("\n-- Top Predictions --")
        for i, p in enumerate(result.predictions[:10]):
            ts = p.timestamp.strftime('%Y-%m-%d') if p.timestamp else "N/A"
            val = p.predicted_value if p.predicted_value is not None else "N/A"
            lines.append(f"[{ts}] {p.symbol}: {val}")

    if result.issues:
        lines.append("\n-- Issues --")
        for issue in result.issues:
            lines.append(f"  - {issue}")

    lines.append("\nDisclaimer: " + result.disclaimer)
    return "\n".join(lines)
