import json
from typing import Any

from bist_signal_bot.data_import.models import (
    ImportSource,
    ColumnMapping,
    SchemaMapping,
    ImportPreview,
    ImportValidationFinding,
    ImportValidationResult,
    NormalizedImportResult,
    ImportJob,
    DataImportReport
)

def source_to_dict(source: ImportSource) -> dict[str, Any]:
    return source.model_dump()

def column_mapping_to_dict(mapping: ColumnMapping) -> dict[str, Any]:
    return mapping.model_dump()

def schema_mapping_to_dict(mapping: SchemaMapping) -> dict[str, Any]:
    return mapping.model_dump()

def preview_to_dict(preview: ImportPreview) -> dict[str, Any]:
    return preview.model_dump()

def validation_finding_to_dict(finding: ImportValidationFinding) -> dict[str, Any]:
    return finding.model_dump()

def validation_to_dict(validation: ImportValidationResult) -> dict[str, Any]:
    return validation.model_dump()

def normalized_result_to_dict(result: NormalizedImportResult) -> dict[str, Any]:
    return result.model_dump()

def job_to_dict(job: ImportJob) -> dict[str, Any]:
    return job.model_dump()

def report_to_dict(report: DataImportReport) -> dict[str, Any]:
    return report.model_dump()

def format_preview_text(preview: ImportPreview) -> str:
    lines = [
        f"Preview ID: {preview.preview_id}",
        f"Rows Estimated: {preview.row_count_estimate or 'Unknown'}",
        f"Columns ({preview.column_count}): {', '.join(preview.columns)}",
        ""
    ]
    if preview.sample_rows:
        lines.append("Sample Row (first):")
        lines.append(json.dumps(preview.sample_rows[0], indent=2))

    lines.append("\n" + preview.disclaimer)
    return "\n".join(lines)

def format_mapping_text(mapping: SchemaMapping) -> str:
    lines = [
        f"Schema Mapping ID: {mapping.schema_mapping_id}",
        f"Status: {mapping.status}",
        f"Confidence: {mapping.confidence_score}%" if mapping.confidence_score else "Confidence: N/A",
        f"Missing Required: {', '.join(mapping.missing_required_targets) if mapping.missing_required_targets else 'None'}",
        ""
    ]
    for m in mapping.column_mappings:
        req_str = "*" if m.required else ""
        lines.append(f"  {m.source_column} -> {m.target_column}{req_str} ({m.semantic_type})")

    lines.append("\n" + mapping.disclaimer)
    return "\n".join(lines)

def format_validation_text(validation: ImportValidationResult) -> str:
    lines = [
        f"Validation ID: {validation.validation_id}",
        f"Status: {validation.status}",
        f"Findings: {len(validation.findings)}",
        ""
    ]
    for f in validation.findings:
        lines.append(f"  [{f.severity}] {f.rule_name}: {f.message}")

    lines.append("\n" + validation.disclaimer)
    return "\n".join(lines)

def format_job_text(job: ImportJob) -> str:
    lines = [
        f"Import Job ID: {job.job_id}",
        f"Status: {job.status}",
        f"Dry Run: {job.dry_run}",
        f"Source: {job.source.path} [{job.source.dataset_type}]",
        ""
    ]
    if job.normalized_result:
        lines.append(f"Output: {job.normalized_result.output_path}")
        lines.append(f"Rows Normalized: {job.normalized_result.row_count}")
        lines.append(f"Duplicates Removed: {job.normalized_result.duplicate_rows_removed}")
        lines.append(f"Invalid Removed: {job.normalized_result.invalid_rows_removed}")

    if job.warnings:
        lines.append("\nWarnings:")
        for w in job.warnings:
            lines.append(f"  - {w}")

    lines.append("\n" + job.disclaimer)
    return "\n".join(lines)

def format_data_import_report_markdown(report: DataImportReport) -> str:
    lines = [
        "# Data Import Report",
        f"Generated: {report.generated_at}",
        "",
        "## Summary",
        f"- Total Jobs: {len(report.jobs)}",
        f"- Total Validations: {len(report.validations)}",
        ""
    ]

    if report.key_findings:
        lines.append("## Key Findings")
        for f in report.key_findings:
            lines.append(f"- {f}")
        lines.append("")

    lines.append("## Recent Jobs")
    for job in report.jobs[:5]:
        lines.append(f"- **{job.job_id}** ({job.status}): {job.source.dataset_type} from {job.source.path}")

    lines.append("\n" + report.disclaimer)
    return "\n".join(lines)

def render_data_import_template(context: dict) -> dict:
    from bist_signal_bot.report_templates.models import RenderedReportSection, ReportValidationStatus
    return {
        "rendered_section_id": "sec_import",
        "section_key": "data_import",
        "title": "Data Import Report",
        "content_markdown": "*Data Import summary.*",
        "content_json": {"status": "PASS"},
        "status": ReportValidationStatus.PASS,
        "warnings": []
    }
