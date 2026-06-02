from typing import Any, Dict
from bist_signal_bot.report_templates.models import (
    ReportSectionDefinition, ReportTemplate, RenderedReportSection, ComposedReport,
    ReportNarrativeBlock, ReportExportArtifact, ReportExportPack, ReportManifest,
    ReportTemplateValidationResult, ReportTemplatesReport
)

def section_definition_to_dict(section: ReportSectionDefinition) -> Dict[str, Any]:
    return section.model_dump(mode="json")

def template_to_dict(template: ReportTemplate) -> Dict[str, Any]:
    return template.model_dump(mode="json")

def rendered_section_to_dict(section: RenderedReportSection) -> Dict[str, Any]:
    return section.model_dump(mode="json")

def composed_report_to_dict(report: ComposedReport) -> Dict[str, Any]:
    return report.model_dump(mode="json")

def narrative_block_to_dict(block: ReportNarrativeBlock) -> Dict[str, Any]:
    return block.model_dump(mode="json")

def export_artifact_to_dict(artifact: ReportExportArtifact) -> Dict[str, Any]:
    return artifact.model_dump(mode="json")

def export_pack_to_dict(pack: ReportExportPack) -> Dict[str, Any]:
    return pack.model_dump(mode="json")

def manifest_to_dict(manifest: ReportManifest) -> Dict[str, Any]:
    return manifest.model_dump(mode="json")

def validation_to_dict(result: ReportTemplateValidationResult) -> Dict[str, Any]:
    return result.model_dump(mode="json")

def report_templates_report_to_dict(report: ReportTemplatesReport) -> Dict[str, Any]:
    return report.model_dump(mode="json")

def format_template_text(template: ReportTemplate) -> str:
    lines = [
        f"Template: {template.name} ({template.kind.value})",
        f"Status: {template.status.value}",
        f"Sections: {len(template.sections)}",
        f"Required: {', '.join(template.required_sections) if template.required_sections else 'None'}"
    ]
    return "\n".join(lines)

def format_composed_report_text(report: ComposedReport) -> str:
    lines = [
        f"Report ID: {report.report_id}",
        f"Template: {report.template_name}",
        f"Status: {report.status.value}",
        f"Sections Rendered: {len(report.sections)}"
    ]
    if report.warnings:
        lines.append("Warnings:")
        for w in report.warnings:
            lines.append(f" - {w}")
    lines.append(f"\nDisclaimer: {report.disclaimer}")
    return "\n".join(lines)

def format_export_pack_text(pack: ReportExportPack) -> str:
    lines = [
        f"Pack ID: {pack.pack_id}",
        f"Report ID: {pack.report_id}",
        f"Artifacts: {len(pack.artifacts)}",
        f"Status: {pack.status.value}"
    ]
    return "\n".join(lines)

def format_manifest_text(manifest: ReportManifest) -> str:
    lines = [
        f"Manifest ID: {manifest.manifest_id}",
        f"Report ID: {manifest.report_id}",
        f"Template: {manifest.template_id}",
        f"Artifacts: {len(manifest.artifact_refs)}"
    ]
    return "\n".join(lines)

def format_validation_text(result: ReportTemplateValidationResult) -> str:
    lines = [
        f"Validation Status: {result.status.value}",
        f"Findings: {len(result.findings)}",
        f"Unsafe Language: {len(result.unsafe_language_findings)}",
        f"Missing Required: {len(result.missing_required_sections)}"
    ]
    return "\n".join(lines)

def format_report_templates_report_markdown(report: ReportTemplatesReport) -> str:
    lines = [
        f"# Report Templates Report",
        f"Date: {report.generated_at.isoformat()}",
        "",
        "## Summary",
        f"- Templates: {len(report.templates)}",
        f"- Composed Reports: {len(report.composed_reports)}",
        f"- Export Packs: {len(report.export_packs)}",
        f"- Validations: {len(report.validations)}",
    ]
    if report.key_findings:
        lines.append("\n## Key Findings")
        for f in report.key_findings:
            lines.append(f"- {f}")

    lines.append(f"\n> *{report.disclaimer}*")
    return "\n".join(lines)
