from typing import Any

import pandas as pd

from bist_signal_bot.data_catalog.models import (
    DataCatalogReport,
    DataLineageEdge,
    DataQualityAssessment,
    DataQualityFinding,
    DataQualityGateResult,
    DatasetContract,
    DatasetProfile,
    DatasetRecord,
    SchemaDriftFinding,
    SourceProvenance,
)


def contract_to_dict(contract: DatasetContract) -> dict[str, Any]:
    return contract.model_dump(mode="json")

def dataset_record_to_dict(record: DatasetRecord) -> dict[str, Any]:
    return record.model_dump(mode="json")

def profile_to_dict(profile: DatasetProfile) -> dict[str, Any]:
    return profile.model_dump(mode="json")

def quality_finding_to_dict(finding: DataQualityFinding) -> dict[str, Any]:
    return finding.model_dump(mode="json")

def quality_assessment_to_dict(assessment: DataQualityAssessment) -> dict[str, Any]:
    return assessment.model_dump(mode="json")

def drift_finding_to_dict(finding: SchemaDriftFinding) -> dict[str, Any]:
    return finding.model_dump(mode="json")

def lineage_edge_to_dict(edge: DataLineageEdge) -> dict[str, Any]:
    return edge.model_dump(mode="json")

def provenance_to_dict(provenance: SourceProvenance) -> dict[str, Any]:
    return provenance.model_dump(mode="json")

def gate_result_to_dict(result: DataQualityGateResult) -> dict[str, Any]:
    return result.model_dump(mode="json")

def catalog_report_to_dict(report: DataCatalogReport) -> dict[str, Any]:
    return report.model_dump(mode="json")

def datasets_to_dataframe(records: list[DatasetRecord]) -> pd.DataFrame:
    data = [dataset_record_to_dict(r) for r in records]
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

def quality_assessments_to_dataframe(assessments: list[DataQualityAssessment]) -> pd.DataFrame:
    data = [quality_assessment_to_dict(a) for a in assessments]
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

def format_dataset_record_text(record: DatasetRecord) -> str:
    lines = [
        f"Dataset: {record.name} ({record.dataset_kind.value})",
        f"ID: {record.dataset_id}",
        f"Format: {record.dataset_format.value}",
        f"Status: {record.status.value}",
        f"Registered: {record.registered_at.isoformat()}"
    ]
    if record.row_count is not None:
         lines.append(f"Rows: {record.row_count}")
    return "\n".join(lines)

def format_profile_text(profile: DatasetProfile) -> str:
    lines = [
        f"Profile ID: {profile.profile_id}",
        f"Format: {profile.detected_format.value}",
        f"Rows: {profile.row_count}, Columns: {profile.column_count}",
        f"Duplicates: {profile.duplicate_count}",
        "Columns:"
    ]
    for c in profile.columns[:10]:
         lines.append(f" - {c}")
    if len(profile.columns) > 10:
         lines.append(f" - ... and {len(profile.columns) - 10} more")
    return "\n".join(lines)

def format_quality_assessment_text(assessment: DataQualityAssessment) -> str:
    lines = [
        f"Assessment ID: {assessment.assessment_id}",
        f"Status: {assessment.status.value}",
        f"Score: {assessment.quality_score if assessment.quality_score is not None else 'N/A'}",
        f"Findings: {len(assessment.findings)}",
        f"Disclaimer: {assessment.disclaimer}"
    ]
    return "\n".join(lines)

def format_drift_findings_text(findings: list[SchemaDriftFinding]) -> str:
    if not findings:
        return "No schema drift detected."
    lines = [f"Found {len(findings)} schema drift issues:"]
    for f in findings:
         lines.append(f" - [{f.severity}] {f.drift_type.value}: {f.message}")
    return "\n".join(lines)

def format_lineage_text(edges: list[DataLineageEdge]) -> str:
    if not edges:
        return "No lineage information available."
    lines = ["Lineage Edges:"]
    for e in edges:
         lines.append(f" - {e.from_dataset_id} --[{e.relation_type.value}]--> {e.to_dataset_id}")
    return "\n".join(lines)

def format_data_catalog_report_markdown(report: DataCatalogReport) -> str:
    lines = [
        "# Data Catalog & Quality Report",
        f"**Generated At**: {report.generated_at.isoformat()}",
        f"**Disclaimer**: {report.disclaimer}",
        "",
        "## Summary",
        f"- **Datasets Registered**: {len(report.datasets)}",
        f"- **Quality Assessments**: {len(report.assessments)}",
        f"- **Schema Drift Findings**: {len(report.drift_findings)}",
        "",
        "## Datasets"
    ]
    for ds in report.datasets:
        lines.append(f"### {ds.name} ({ds.dataset_id})")
        lines.append(f"- Kind: {ds.dataset_kind.value}")
        lines.append(f"- Status: {ds.status.value}")
        lines.append("")

    lines.append("## Quality Gates")
    for gate in report.gates:
        lines.append(f"- Gate **{gate.gate_name}**: {gate.status.value} (Score: {gate.actual_score})")

    return "\n".join(lines)

def render_data_quality_template(context: dict) -> dict:
    from bist_signal_bot.report_templates.models import RenderedReportSection, ReportValidationStatus
    return {
        "rendered_section_id": "sec_dq",
        "section_key": "data_quality",
        "title": "Data Quality Report",
        "content_markdown": "*Data Quality summary.*",
        "content_json": {"status": "PASS"},
        "status": ReportValidationStatus.PASS,
        "warnings": []
    }
