from typing import Any
from bist_signal_bot.explainability.models import (
    FeatureAttribution,
    LocalExplanation,
    GlobalExplanation,
    SensitivityPoint,
    SensitivityAnalysisResult,
    DecisionTraceStep,
    DecisionTrace,
    RuleTrace,
    CounterfactualScenario,
    ExplanationCohort,
    ExplanationGovernanceAssessment,
    ExplainabilityReport
)

def attribution_to_dict(attribution: FeatureAttribution) -> dict[str, Any]:
    return attribution.model_dump(mode='json')

def local_explanation_to_dict(explanation: LocalExplanation) -> dict[str, Any]:
    return explanation.model_dump(mode='json')

def global_explanation_to_dict(explanation: GlobalExplanation) -> dict[str, Any]:
    return explanation.model_dump(mode='json')

def sensitivity_point_to_dict(point: SensitivityPoint) -> dict[str, Any]:
    return point.model_dump(mode='json')

def sensitivity_result_to_dict(result: SensitivityAnalysisResult) -> dict[str, Any]:
    return result.model_dump(mode='json')

def decision_step_to_dict(step: DecisionTraceStep) -> dict[str, Any]:
    return step.model_dump(mode='json')

def decision_trace_to_dict(trace: DecisionTrace) -> dict[str, Any]:
    return trace.model_dump(mode='json')

def rule_trace_to_dict(trace: RuleTrace) -> dict[str, Any]:
    return trace.model_dump(mode='json')

def counterfactual_to_dict(counterfactual: CounterfactualScenario) -> dict[str, Any]:
    return counterfactual.model_dump(mode='json')

def cohort_to_dict(cohort: ExplanationCohort) -> dict[str, Any]:
    return cohort.model_dump(mode='json')

def governance_to_dict(assessment: ExplanationGovernanceAssessment) -> dict[str, Any]:
    return assessment.model_dump(mode='json')

def report_to_dict(report: ExplainabilityReport) -> dict[str, Any]:
    return report.model_dump(mode='json')

def format_local_explanation_text(explanation: LocalExplanation) -> str:
    lines = [f"Local Explanation for {explanation.object_id} (Symbol: {explanation.symbol})"]
    lines.append(f"Status: {explanation.status.value}")
    if explanation.prediction_value is not None:
        lines.append(f"Prediction: {explanation.prediction_value:.4f}")
    lines.append("Top Drivers:")
    for a in explanation.attributions[:5]:
        score = a.contribution_score if a.contribution_score is not None else 0.0
        lines.append(f"  - {a.feature_name}: {score:.4f} ({a.direction.value})")
    lines.append(f"\nDisclaimer: {explanation.disclaimer}")
    return "\n".join(lines)

def format_global_explanation_text(explanation: GlobalExplanation) -> str:
    lines = [f"Global Explanation for {explanation.object_id}"]
    lines.append(f"Status: {explanation.status.value}")
    lines.append(f"Sample Count: {explanation.sample_count}")
    lines.append("Top Features:")
    for f in explanation.top_features:
        lines.append(f"  - {f}")
    lines.append(f"\nDisclaimer: {explanation.disclaimer}")
    return "\n".join(lines)

def format_sensitivity_text(result: SensitivityAnalysisResult) -> str:
    lines = [f"Sensitivity Analysis for {result.feature_name} (Symbol: {result.symbol})"]
    lines.append(f"Status: {result.status.value}")
    if result.monotonicity_hint:
        lines.append(f"Monotonicity: {result.monotonicity_hint}")
    lines.append("Points:")
    for p in result.points:
        orig = p.original_value if p.original_value is not None else "N/A"
        pert = p.perturbed_value if p.perturbed_value is not None else "N/A"
        delta = p.delta_output if p.delta_output is not None else "N/A"
        lines.append(f"  - Value: {orig} -> {pert} | Delta Output: {delta}")
    lines.append(f"\nDisclaimer: {result.disclaimer}")
    return "\n".join(lines)

def format_decision_trace_text(trace: DecisionTrace) -> str:
    lines = [f"Decision Trace for {trace.object_id} (Symbol: {trace.symbol})"]
    lines.append(f"Status: {trace.status.value}")
    lines.append("Steps:")
    for s in trace.steps:
        lines.append(f"  - {s.step_name}: {'PASS' if s.passed else 'FAIL/UNKNOWN'} - {s.message}")
    lines.append(f"\nDisclaimer: {trace.disclaimer}")
    return "\n".join(lines)

def format_rule_trace_text(trace: RuleTrace) -> str:
    lines = [f"Rule Trace for {trace.strategy_name} (Symbol: {trace.symbol})"]
    lines.append(f"Status: {trace.status.value}")
    lines.append(f"Passed: {trace.passed_rules}, Failed: {trace.failed_rules}")
    lines.append("Rules Evaluated:")
    for s in trace.rules_evaluated:
        lines.append(f"  - {s.step_name}: {'PASS' if s.passed else 'FAIL'}")
    lines.append(f"\nDisclaimer: {trace.disclaimer}")
    return "\n".join(lines)

def format_counterfactuals_text(items: list[CounterfactualScenario]) -> str:
    if not items:
        return "No counterfactual scenarios."
    lines = [f"Counterfactual Scenarios (Count: {len(items)})"]
    for item in items:
        lines.append(f"  - Scenario {item.counterfactual_id}: Status {item.plausibility_status.value}")
        lines.append(f"    Changes: {item.changed_features}")
        lines.append(f"    Delta Output: {item.delta_output}")
    lines.append(f"\nDisclaimer: {items[0].disclaimer}")
    return "\n".join(lines)

def format_explainability_report_markdown(report: ExplainabilityReport, *args, **kwargs) -> str:
    lines = ["# Explainability Report"]
    lines.append(f"Generated at: {report.generated_at.isoformat()}")

    lines.append("\n## Global Explanations")
    for g in report.global_explanations:
        lines.append(format_global_explanation_text(g))

    lines.append("\n## Governance")
    for a in report.governance_assessments:
        lines.append(f"- {a.object_id}: {a.status.value}")
        if a.unsafe_language_findings:
            lines.append(f"  - Unsafe findings: {', '.join(a.unsafe_language_findings)}")

    lines.append(f"\n## Disclaimer\n{report.disclaimer}")
    return "\n".join(lines)

def format_explainability_report(report: Any, *args, **kwargs) -> str:
    return "Explainability Report Summary"
