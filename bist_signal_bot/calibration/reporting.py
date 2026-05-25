import pandas as pd
from typing import Any
from bist_signal_bot.calibration.models import (
    OutcomeRecord, CalibrationBin, CalibrationMetric, ReliabilityCurve, CalibrationResult,
    ThresholdPolicy, ThresholdOptimizationResult, OutcomeCohort, ErrorCase, CalibrationReport
)

def outcome_record_to_dict(record: OutcomeRecord) -> dict[str, Any]:
    d = record.model_dump()
    if d.get("generated_at"): d["generated_at"] = d["generated_at"].isoformat()
    if d.get("evaluated_at"): d["evaluated_at"] = d["evaluated_at"].isoformat()
    return d

def calibration_bin_to_dict(bin: CalibrationBin) -> dict[str, Any]:
    return bin.model_dump()

def calibration_metric_to_dict(metric: CalibrationMetric) -> dict[str, Any]:
    return metric.model_dump()

def reliability_curve_to_dict(curve: ReliabilityCurve) -> dict[str, Any]:
    d = curve.model_dump()
    d["bins"] = [calibration_bin_to_dict(b) for b in curve.bins]
    return d

def calibration_result_to_dict(result: CalibrationResult) -> dict[str, Any]:
    d = result.model_dump()
    if d.get("generated_at"): d["generated_at"] = d["generated_at"].isoformat()
    d["bins"] = [calibration_bin_to_dict(b) for b in result.bins]
    d["metrics"] = [calibration_metric_to_dict(m) for m in result.metrics]
    if result.reliability_curve:
        d["reliability_curve"] = reliability_curve_to_dict(result.reliability_curve)
    return d

def threshold_policy_to_dict(policy: ThresholdPolicy) -> dict[str, Any]:
    d = policy.model_dump()
    if d.get("created_at"): d["created_at"] = d["created_at"].isoformat()
    return d

def threshold_result_to_dict(result: ThresholdOptimizationResult) -> dict[str, Any]:
    d = result.model_dump()
    d["candidate_thresholds"] = [threshold_policy_to_dict(p) for p in result.candidate_thresholds]
    if result.selected_threshold:
        d["selected_threshold"] = threshold_policy_to_dict(result.selected_threshold)
    return d

def cohort_to_dict(cohort: OutcomeCohort) -> dict[str, Any]:
    return cohort.model_dump()

def error_case_to_dict(error: ErrorCase) -> dict[str, Any]:
    return error.model_dump()

def calibration_report_to_dict(report: CalibrationReport) -> dict[str, Any]:
    d = report.model_dump()
    if d.get("generated_at"): d["generated_at"] = d["generated_at"].isoformat()
    d["results"] = [calibration_result_to_dict(r) for r in report.results]
    d["threshold_results"] = [threshold_result_to_dict(r) for r in report.threshold_results]
    d["cohorts"] = [cohort_to_dict(c) for c in report.cohorts]
    d["error_cases"] = [error_case_to_dict(e) for e in report.error_cases]
    return d

def outcomes_to_dataframe(records: list[OutcomeRecord]) -> pd.DataFrame:
    return pd.DataFrame([outcome_record_to_dict(r) for r in records])

def bins_to_dataframe(bins: list[CalibrationBin]) -> pd.DataFrame:
    return pd.DataFrame([calibration_bin_to_dict(b) for b in bins])

def errors_to_dataframe(errors: list[ErrorCase]) -> pd.DataFrame:
    return pd.DataFrame([error_case_to_dict(e) for e in errors])

def format_calibration_result_text(result: CalibrationResult) -> str:
    lines = [f"### Calibration Result: {result.score_type.value} ({result.horizon.value})"]
    lines.append(f"- Status: {result.status.value}")
    lines.append(f"- Sample Count: {result.sample_count}")
    if result.warnings:
        lines.append("- Warnings:")
        for w in result.warnings:
            lines.append(f"  * {w}")
    lines.append(f"\n_{result.disclaimer}_")
    return "\n".join(lines)

def format_reliability_curve_text(curve: ReliabilityCurve) -> str:
    lines = [f"### Reliability Curve: {curve.score_type.value}"]
    lines.append(f"- Status: {curve.status.value}")
    if curve.expected_calibration_error is not None:
        lines.append(f"- ECE: {curve.expected_calibration_error:.4f}")
    if curve.max_calibration_error is not None:
        lines.append(f"- MCE: {curve.max_calibration_error:.4f}")
    lines.append(f"\n_{curve.disclaimer}_")
    return "\n".join(lines)

def format_threshold_result_text(result: ThresholdOptimizationResult) -> str:
    lines = [f"### Threshold Optimization: {result.score_type.value}"]
    lines.append(f"- Objective: {result.objective_name}")
    if result.selected_threshold:
        lines.append(f"- Selected Threshold: {result.selected_threshold.threshold_value}")
        lines.append(f"- Expected Reduction: {result.selected_threshold.expected_signal_reduction_pct:.2f}%")
    else:
        lines.append("- No valid threshold selected.")
    lines.append(f"\n_{result.disclaimer}_")
    return "\n".join(lines)

def format_cohorts_text(cohorts: list[OutcomeCohort]) -> str:
    lines = ["### Outcome Cohorts"]
    for c in cohorts:
        lines.append(f"- {c.name}: {c.sample_count} samples, Status: {c.status.value}")
    return "\n".join(lines)

def format_error_cases_text(errors: list[ErrorCase]) -> str:
    lines = ["### Error Cases"]
    for e in errors[:10]:
        lines.append(f"- {e.symbol} ({e.error_type.value}): {e.message}")
    if len(errors) > 10:
        lines.append(f"... and {len(errors) - 10} more.")
    return "\n".join(lines)

def format_calibration_report_markdown(report: CalibrationReport) -> str:
    sections = [
        f"# BIST Bot Calibration Report",
        f"Generated At: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"Overall Status: {report.overall_status.value}\n"
    ]

    if report.key_findings:
        sections.append("## Key Findings")
        for f in report.key_findings:
            sections.append(f"- {f}")
        sections.append("")

    sections.append("## Reliability Curves")
    for r in report.results:
        if r.reliability_curve:
            sections.append(format_reliability_curve_text(r.reliability_curve))

    sections.append("\n## Thresholds")
    for t in report.threshold_results:
        sections.append(format_threshold_result_text(t))

    sections.append("\n## Weak Cohorts")
    weak = [c for c in report.cohorts if c.status.value in ["FAIL", "WATCH"]]
    sections.append(format_cohorts_text(weak))

    sections.append("\n## Notable Errors")
    sections.append(format_error_cases_text(report.error_cases))

    sections.append(f"\n---\n_{report.disclaimer}_")

    return "\n".join(sections)
