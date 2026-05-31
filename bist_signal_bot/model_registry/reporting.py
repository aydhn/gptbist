from typing import Any
import pandas as pd
from datetime import datetime

from bist_signal_bot.model_registry.models import (
    ModelRecord, ExperimentRun, ModelArtifact, ModelCard,
    ModelValidationSummary, ModelCalibrationSummary, ModelPromotionRequest,
    ModelDriftFinding, ModelLineageEdge, ModelGovernanceAssessment, ModelRegistryReport
)


def model_record_to_dict(model: ModelRecord) -> dict[str, Any]:
    return {
        "model_id": model.model_id,
        "model_name": model.model_name,
        "model_kind": model.model_kind.value,
        "version": model.version,
        "status": model.status.value,
        "created_at": model.created_at.isoformat(),
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
        "feature_set_version": model.feature_set_version,
        "warnings": model.warnings
    }

def experiment_run_to_dict(run: ExperimentRun) -> dict[str, Any]:
    return {
        "run_id": run.run_id,
        "experiment_name": run.experiment_name,
        "model_name": run.model_name,
        "status": run.status.value,
        "started_at": run.started_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "metrics": run.metrics
    }

def artifact_to_dict(artifact: ModelArtifact) -> dict[str, Any]:
    return {
        "artifact_id": artifact.artifact_id,
        "model_id": artifact.model_id,
        "path": artifact.path,
        "format": artifact.artifact_format.value,
        "created_at": artifact.created_at.isoformat(),
        "size_bytes": artifact.size_bytes,
        "loadable": artifact.loadable
    }

def model_card_to_dict(card: ModelCard) -> dict[str, Any]:
    return {
        "card_id": card.card_id,
        "model_id": card.model_id,
        "model_name": card.model_name,
        "version": card.version,
        "governance_status": card.governance_status.value,
        "created_at": card.created_at.isoformat()
    }

def validation_summary_to_dict(summary: ModelValidationSummary) -> dict[str, Any]:
    return {
        "validation_id": summary.validation_id,
        "model_id": summary.model_id,
        "method": summary.validation_method,
        "status": summary.status.value,
        "leakage_status": summary.leakage_status.value,
        "feature_quality": summary.feature_quality_score,
        "metrics": summary.metrics
    }

def calibration_summary_to_dict(summary: ModelCalibrationSummary) -> dict[str, Any]:
    return {
        "calibration_id": summary.calibration_id,
        "model_id": summary.model_id,
        "method": summary.calibration_method,
        "status": summary.status.value,
        "reliability_score": summary.reliability_score,
        "ece": summary.expected_calibration_error
    }

def promotion_request_to_dict(request: ModelPromotionRequest) -> dict[str, Any]:
    return {
        "promotion_id": request.promotion_id,
        "model_id": request.model_id,
        "requested_stage": request.requested_stage.value,
        "current_stage": request.current_stage.value,
        "approved": request.approved,
        "reason": request.reason,
        "governance_decision": request.governance_decision.value
    }

def drift_finding_to_dict(finding: ModelDriftFinding) -> dict[str, Any]:
    return {
        "drift_id": finding.drift_id,
        "model_id": finding.model_id,
        "drift_type": finding.drift_type.value,
        "score": finding.drift_score,
        "status": finding.status.value,
        "message": finding.message
    }

def lineage_edge_to_dict(edge: ModelLineageEdge) -> dict[str, Any]:
    return {
        "edge_id": edge.edge_id,
        "from": edge.from_object_id,
        "to": edge.to_object_id,
        "relation": edge.relation,
        "process": edge.process_name
    }

def governance_assessment_to_dict(assessment: ModelGovernanceAssessment) -> dict[str, Any]:
    return {
        "assessment_id": assessment.assessment_id,
        "model_id": assessment.model_id,
        "status": assessment.status.value,
        "blocking_reasons": assessment.blocking_reasons,
        "created_at": assessment.created_at.isoformat()
    }

def model_registry_report_to_dict(report: ModelRegistryReport) -> dict[str, Any]:
    return {
        "report_id": report.report_id,
        "generated_at": report.generated_at.isoformat(),
        "models_count": len(report.models),
        "experiments_count": len(report.experiments),
        "artifacts_count": len(report.artifacts),
        "cards_count": len(report.cards),
        "drift_findings": len(report.drift_findings),
        "key_findings": report.key_findings
    }

def models_to_dataframe(models: list[ModelRecord]) -> pd.DataFrame:
    data = [model_record_to_dict(m) for m in models]
    return pd.DataFrame(data)

def experiments_to_dataframe(runs: list[ExperimentRun]) -> pd.DataFrame:
    data = [experiment_run_to_dict(r) for r in runs]
    # Flatten metrics
    flat_data = []
    for d in data:
        metrics = d.pop("metrics")
        for k, v in metrics.items():
            d[f"metric_{k}"] = v
        flat_data.append(d)
    return pd.DataFrame(flat_data)

def format_model_record_text(model: ModelRecord) -> str:
    lines = [
        f"Model: {model.model_name} (v{model.version})",
        f"ID: {model.model_id}",
        f"Kind: {model.model_kind.value}",
        f"Status: {model.status.value}",
        f"Created: {model.created_at.isoformat()}"
    ]
    if model.feature_set_version:
        lines.append(f"Feature Version: {model.feature_set_version}")
    if model.warnings:
        lines.append("Warnings:")
        for w in model.warnings:
            lines.append(f"  - {w}")
    lines.append(f"Disclaimer: {model.disclaimer}")
    return "\n".join(lines)

def format_experiment_run_text(run: ExperimentRun) -> str:
    lines = [
        f"Experiment: {run.experiment_name} | Model: {run.model_name}",
        f"Run ID: {run.run_id}",
        f"Status: {run.status.value}",
        f"Duration: {(run.finished_at - run.started_at).total_seconds() if run.finished_at else 'Running'}s"
    ]
    if run.metrics:
        lines.append("Metrics:")
        for k, v in run.metrics.items():
            lines.append(f"  {k}: {v:.4f}")
    lines.append(f"Disclaimer: {run.disclaimer}")
    return "\n".join(lines)

def format_model_card_markdown(card: ModelCard) -> str:
    # Usually this logic is in ModelCardBuilder.render_markdown
    # If the user asks for it here, we will just call that logic, or replicate it.
    from bist_signal_bot.model_registry.model_cards import ModelCardBuilder
    return ModelCardBuilder().render_markdown(card)

def format_validation_summary_text(summary: ModelValidationSummary) -> str:
    lines = [
        f"Validation: {summary.validation_id} for Model: {summary.model_id}",
        f"Method: {summary.validation_method}",
        f"Status: {summary.status.value}",
        f"Leakage Status: {summary.leakage_status.value}",
        f"Feature Quality: {summary.feature_quality_score}"
    ]
    if summary.metrics:
        lines.append("Metrics:")
        for k, v in summary.metrics.items():
            lines.append(f"  {k}: {v:.4f}")
    if summary.overfit_warnings:
        lines.append("Overfit Warnings:")
        for w in summary.overfit_warnings:
            lines.append(f"  - {w}")
    lines.append(f"Disclaimer: {summary.disclaimer}")
    return "\n".join(lines)

def format_calibration_summary_text(summary: ModelCalibrationSummary) -> str:
    lines = [
        f"Calibration: {summary.calibration_id} for Model: {summary.model_id}",
        f"Method: {summary.calibration_method}",
        f"Status: {summary.status.value}",
        f"Reliability Score: {summary.reliability_score}",
        f"ECE: {summary.expected_calibration_error}"
    ]
    if summary.warnings:
        lines.append("Warnings:")
        for w in summary.warnings:
            lines.append(f"  - {w}")
    lines.append(f"Disclaimer: {summary.disclaimer}")
    return "\n".join(lines)

def format_governance_assessment_text(assessment: ModelGovernanceAssessment) -> str:
    lines = [
        f"Governance Assessment for Model: {assessment.model_id}",
        f"Overall Status: {assessment.status.value}",
        f"Artifact: {assessment.artifact_status.value if assessment.artifact_status else 'N/A'}",
        f"Card: {assessment.model_card_status.value if assessment.model_card_status else 'N/A'}",
        f"Validation: {assessment.validation_status.value if assessment.validation_status else 'N/A'}",
        f"Calibration: {assessment.calibration_status.value if assessment.calibration_status else 'N/A'}",
        f"Leakage: {assessment.leakage_status.value if assessment.leakage_status else 'N/A'}"
    ]
    if assessment.blocking_reasons:
        lines.append("Blocking Reasons:")
        for r in assessment.blocking_reasons:
            lines.append(f"  - {r}")
    lines.append(f"Disclaimer: {assessment.disclaimer}")
    return "\n".join(lines)

def format_model_registry_report_markdown(report: ModelRegistryReport) -> str:
    lines = [
        f"# Model Registry Report",
        f"Generated At: {report.generated_at.isoformat()}",
        "",
        "## Summary",
        f"- Models: {len(report.models)}",
        f"- Experiments: {len(report.experiments)}",
        f"- Artifacts: {len(report.artifacts)}",
        f"- Model Cards: {len(report.cards)}",
        f"- Drift Findings: {len(report.drift_findings)}",
        "",
        "## Key Findings",
        *[f"- {f}" for f in report.key_findings],
        "",
        "## Warnings",
        *[f"- {w}" for w in report.warnings],
        "",
        "---",
        f"**Disclaimer:** {report.disclaimer}"
    ]
    return "\n".join(lines)
