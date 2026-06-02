import uuid
from typing import Any, Dict, List, Optional
from bist_signal_bot.report_templates.models import (
    ReportTemplate, ReportTemplateKind, ReportTemplateStatus, ReportOutputFormat, ReportSectionDefinition
)
from bist_signal_bot.report_templates.sections import ReportSectionLibrary

class ReportTemplateLibrary:
    def __init__(self, settings=None):
        self.settings = settings
        self.section_lib = ReportSectionLibrary(settings)
        self._templates = {t.name: t for t in self.default_templates()}

    def default_templates(self) -> List[ReportTemplate]:
        sections = self.section_lib.default_sections()
        defaults = [
            ("daily_research_report_v1", ReportTemplateKind.DAILY),
            ("weekly_operator_report_v1", ReportTemplateKind.WEEKLY),
            ("monthly_governance_report_v1", ReportTemplateKind.MONTHLY),
            ("data_quality_report_v1", ReportTemplateKind.DATA_QUALITY),
            ("feature_quality_report_v1", ReportTemplateKind.FEATURE_QUALITY),
            ("model_governance_report_v1", ReportTemplateKind.MODEL_GOVERNANCE),
            ("monitoring_report_v1", ReportTemplateKind.MONITORING),
            ("leaderboard_report_v1", ReportTemplateKind.LEADERBOARD),
            ("orchestrator_report_v1", ReportTemplateKind.ORCHESTRATOR),
            ("final_audit_report_v1", ReportTemplateKind.FINAL_AUDIT),
            ("final_handoff_report_v1", ReportTemplateKind.FINAL_HANDOFF),
            ("performance_report_v1", ReportTemplateKind.PERFORMANCE),
            ("data_import_report_v1", ReportTemplateKind.DATA_IMPORT),
        ]

        return [
            ReportTemplate(
                template_id=f"tpl_{uuid.uuid4().hex[:8]}",
                name=name,
                kind=kind,
                version="1.0.0",
                description=f"Default {kind.value} template",
                sections=sections,
                default_output_formats=[ReportOutputFormat.MARKDOWN, ReportOutputFormat.JSON],
                required_sections=["summary", "disclaimer"],
                optional_sections=["warnings", "status_table"],
                status=ReportTemplateStatus.ACTIVE
            ) for name, kind in defaults
        ]

    def get_template(self, template_id_or_name: str) -> Optional[ReportTemplate]:
        for t in self._templates.values():
            if t.template_id == template_id_or_name or t.name == template_id_or_name:
                return t
        return None

    def templates_by_kind(self, kind: ReportTemplateKind) -> List[ReportTemplate]:
        return [t for t in self._templates.values() if t.kind == kind]

    def validate_template(self, template: ReportTemplate) -> List[str]:
        findings = []
        if not template.sections:
            findings.append("Template has no sections.")
        section_keys = [s.section_key for s in template.sections]
        if len(set(section_keys)) != len(section_keys):
            findings.append("Duplicate section_key found.")
        for req in template.required_sections:
            if req not in section_keys:
                findings.append(f"Required section {req} is missing from sections list.")
        if "disclaimer" not in section_keys:
            findings.append("Disclaimer section is required.")
        return findings

    def template_summary(self, template: ReportTemplate) -> Dict[str, Any]:
        return {
            "template_id": template.template_id,
            "name": template.name,
            "kind": template.kind.value,
            "sections_count": len(template.sections),
            "valid": len(self.validate_template(template)) == 0
        }
