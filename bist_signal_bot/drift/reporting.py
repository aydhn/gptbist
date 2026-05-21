import pandas as pd
from typing import Any
from bist_signal_bot.drift.models import (
    DriftAnalysisResult, FeatureDriftResult, ModelDriftResult,
    CalibrationReport, SignalDecayReport, StrategyDecayReport, PortfolioDriftReport, DriftMetric
)

def drift_result_to_dict(result: DriftAnalysisResult) -> dict[str, Any]:
    return result.safe_public_dict()

def feature_drift_to_dict(result: FeatureDriftResult) -> dict[str, Any]:
    return result.model_dump(mode='json')

def model_drift_to_dict(result: ModelDriftResult) -> dict[str, Any]:
    return result.model_dump(mode='json')

def calibration_report_to_dict(report: CalibrationReport) -> dict[str, Any]:
    return report.model_dump(mode='json')

def signal_decay_to_dict(report: SignalDecayReport) -> dict[str, Any]:
    return report.model_dump(mode='json')

def strategy_decay_to_dict(report: StrategyDecayReport) -> dict[str, Any]:
    return report.model_dump(mode='json')

def portfolio_drift_to_dict(report: PortfolioDriftReport) -> dict[str, Any]:
    return report.model_dump(mode='json')

def feature_results_to_dataframe(results: list[FeatureDriftResult]) -> pd.DataFrame:
    rows = []
    for r in results:
        row = {"feature_name": r.feature_name, "status": r.status.value, "severity": r.severity.value}
        for m in r.metrics:
            row[f"{m.metric_name}_val"] = m.value
        rows.append(row)
    return pd.DataFrame(rows)

def drift_metrics_to_dataframe(metrics: list[DriftMetric]) -> pd.DataFrame:
    rows = [m.model_dump(mode='json') for m in metrics]
    return pd.DataFrame(rows)

def format_drift_result_text(result: DriftAnalysisResult) -> str:
    lines = [
        f"Drift Analysis Report ({result.drift_id})",
        f"Generated: {result.generated_at}",
        f"Status: {result.status.value} (Severity: {result.severity.value})",
        f"Overall Score: {result.overall_drift_score:.2f}" if result.overall_drift_score is not None else "Overall Score: N/A",
        f"\nRecommended Actions: {', '.join([a.value for a in result.recommended_actions])}",
        "\nDomain Summaries:",
        f"- Feature Drift: {len([r for r in result.feature_results if r.status.value in ['DRIFTING', 'SEVERE_DRIFT']])} features drifting",
        f"- Model Drift: {', '.join([r.status.value for r in result.model_results]) if result.model_results else 'N/A'}",
        f"- Signal Decay: {', '.join([r.status.value for r in result.signal_decay_reports]) if result.signal_decay_reports else 'N/A'}",
        f"- Strategy Decay: {', '.join([r.status.value for r in result.strategy_decay_reports]) if result.strategy_decay_reports else 'N/A'}",
        f"- Portfolio Drift: {', '.join([r.status.value for r in result.portfolio_drift_reports]) if result.portfolio_drift_reports else 'N/A'}",
        f"\nDisclaimer: {result.disclaimer}"
    ]
    return "\n".join(lines)

def format_feature_drift_text(results: list[FeatureDriftResult]) -> str:
    drifting = [r for r in results if r.status.value in ['DRIFTING', 'SEVERE_DRIFT']]
    lines = [f"Feature Drift Summary (Total: {len(results)}, Drifting: {len(drifting)})"]
    for r in drifting[:10]:
         lines.append(f"- {r.feature_name}: {r.status.value} ({r.severity.value})")
    if len(drifting) > 10:
         lines.append(f"... and {len(drifting) - 10} more.")
    return "\n".join(lines)

def format_model_drift_text(result: ModelDriftResult) -> str:
    lines = [
        f"Model Drift (Model: {result.model_id or 'Unknown'})",
        f"Status: {result.status.value} (Severity: {result.severity.value})"
    ]
    for m in result.score_distribution_metrics:
        lines.append(f"- {m.metric_name}: {m.value}")
    return "\n".join(lines)

def format_calibration_text(report: CalibrationReport) -> str:
    lines = [
        f"Calibration Report (Model: {report.model_id or 'Unknown'})",
        f"Status: {report.status.value}",
        f"ECE: {report.expected_calibration_error}",
        f"Brier Score: {report.brier_score}",
        f"\nDisclaimer: {report.disclaimer}"
    ]
    return "\n".join(lines)

def format_drift_report_markdown(result: DriftAnalysisResult) -> str:
    md = [
        f"# Drift Analysis Report",
        f"**ID:** {result.drift_id}  ",
        f"**Generated:** {result.generated_at}  ",
        f"**Status:** {result.status.value}  ",
        f"**Severity:** {result.severity.value}  ",
        f"**Overall Score:** {result.overall_drift_score:.2f}" if result.overall_drift_score is not None else "**Overall Score:** N/A  ",
        f"**Recommended Actions:** {', '.join([a.value for a in result.recommended_actions])}  \n",
        f"## Disclaimer",
        f"_{result.disclaimer}_\n"
    ]

    if result.warnings:
         md.append("## Warnings")
         for w in result.warnings:
             md.append(f"- {w}")
         md.append("\n")

    return "\n".join(md)
