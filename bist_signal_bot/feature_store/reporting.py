import pandas as pd
from typing import Any
from bist_signal_bot.feature_store.models import (
    FeatureContract, FeatureDefinition, FeatureSet, FeatureValue, FeatureFrame,
    FeatureQualityAssessment, FeatureQualityFinding, FeatureDriftFinding,
    FeatureLeakageFinding, FeatureLineageEdge, FeatureVersion, FeatureStoreReport
)

def contract_to_dict(contract: FeatureContract) -> dict[str, Any]:
    return contract.model_dump(mode='json')

def feature_definition_to_dict(feature: FeatureDefinition) -> dict[str, Any]:
    return feature.model_dump(mode='json')

def feature_set_to_dict(feature_set: FeatureSet) -> dict[str, Any]:
    return feature_set.model_dump(mode='json')

def feature_value_to_dict(value: FeatureValue) -> dict[str, Any]:
    return value.model_dump(mode='json')

def feature_frame_to_dict(frame: FeatureFrame) -> dict[str, Any]:
    return frame.model_dump(mode='json')

def quality_finding_to_dict(finding: FeatureQualityFinding) -> dict[str, Any]:
    return finding.model_dump(mode='json')

def quality_assessment_to_dict(assessment: FeatureQualityAssessment) -> dict[str, Any]:
    return assessment.model_dump(mode='json')

def drift_finding_to_dict(finding: FeatureDriftFinding) -> dict[str, Any]:
    return finding.model_dump(mode='json')

def leakage_finding_to_dict(finding: FeatureLeakageFinding) -> dict[str, Any]:
    return finding.model_dump(mode='json')

def lineage_edge_to_dict(edge: FeatureLineageEdge) -> dict[str, Any]:
    return edge.model_dump(mode='json')

def version_to_dict(version: FeatureVersion) -> dict[str, Any]:
    return version.model_dump(mode='json')

def feature_store_report_to_dict(report: FeatureStoreReport) -> dict[str, Any]:
    return report.model_dump(mode='json')

def features_to_dataframe(features: list[FeatureDefinition]) -> pd.DataFrame:
    data = [f.model_dump(mode='json') for f in features]
    return pd.DataFrame(data) if data else pd.DataFrame()

def feature_values_to_dataframe(values: list[FeatureValue]) -> pd.DataFrame:
    data = [v.model_dump(mode='json') for v in values]
    return pd.DataFrame(data) if data else pd.DataFrame()

def feature_frame_to_dataframe(frame: FeatureFrame) -> pd.DataFrame:
    return pd.DataFrame(frame.rows) if frame.rows else pd.DataFrame()

def format_feature_definition_text(feature: FeatureDefinition) -> str:
    return f"Feature: {feature.feature_name} (Kind: {feature.feature_kind.value}, Status: {feature.status.value})"

def format_feature_set_text(feature_set: FeatureSet) -> str:
    return f"Feature Set: {feature_set.name} (v{feature_set.version}, Status: {feature_set.status.value}, Features: {len(feature_set.feature_names)})"

def format_quality_assessment_text(assessment: FeatureQualityAssessment) -> str:
    score_str = f"{assessment.quality_score:.1f}" if assessment.quality_score is not None else "N/A"
    lines = [
        f"Quality Assessment: {assessment.status.value} (Score: {score_str})",
        f"Findings: {len(assessment.findings)}",
        f"Disclaimer: {assessment.disclaimer}"
    ]
    return "\n".join(lines)

def format_drift_findings_text(findings: list[FeatureDriftFinding]) -> str:
    if not findings:
        return "No drift findings."
    lines = [f"Drift Findings ({len(findings)}):"]
    for f in findings:
        lines.append(f" - {f.feature_name}: {f.drift_type.value} ({f.message})")
    return "\n".join(lines)

def format_leakage_findings_text(findings: list[FeatureLeakageFinding]) -> str:
    if not findings:
        return "No leakage findings."
    lines = [f"Leakage Findings ({len(findings)}):"]
    for f in findings:
        lines.append(f" - {f.feature_name}: {f.leakage_type.value} [{f.status.value}] ({f.message})")
    return "\n".join(lines)

def format_feature_store_report_markdown(report: FeatureStoreReport) -> str:
    lines = [
        f"# Feature Store Report",
        f"Generated: {report.generated_at.isoformat()}",
        "",
        f"**Disclaimer**: {report.disclaimer}",
        "",
        f"## Summary",
        f"- Features: {len(report.features)}",
        f"- Feature Sets: {len(report.feature_sets)}",
        f"- Quality Assessments: {len(report.quality_assessments)}",
        f"- Drift Findings: {len(report.drift_findings)}",
        f"- Leakage Findings: {len(report.leakage_findings)}",
        ""
    ]
    if report.key_findings:
        lines.append("## Key Findings")
        for k in report.key_findings:
            lines.append(f"- {k}")
    return "\n".join(lines)
