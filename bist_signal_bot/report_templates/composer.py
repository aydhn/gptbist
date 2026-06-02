import uuid
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from bist_signal_bot.report_templates.models import (
    ReportTemplate, ComposedReport, RenderedReportSection, ReportOutputFormat, ReportValidationStatus, ReportTemplateKind
)
from bist_signal_bot.report_templates.library import ReportTemplateLibrary
from bist_signal_bot.report_templates.sections import ReportSectionLibrary

class ReportComposer:
    def __init__(self, settings=None, library=None, section_library=None):
        self.settings = settings
        self.library = library or ReportTemplateLibrary(settings)
        self.section_library = section_library or ReportSectionLibrary(settings)

    def compose(self, template_id_or_name: str, context: Optional[Dict[str, Any]] = None, output_formats: Optional[List[ReportOutputFormat]] = None) -> ComposedReport:
        template = self.library.get_template(template_id_or_name)
        if not template:
            from bist_signal_bot.core.exceptions import ReportComposerError
            raise ReportComposerError(f"Template not found: {template_id_or_name}")
        return self.compose_from_template(template, context, output_formats)

    def compose_from_template(self, template: ReportTemplate, context: Optional[Dict[str, Any]] = None, output_formats: Optional[List[ReportOutputFormat]] = None) -> ComposedReport:
        ctx = context or self.collect_context(template.kind)
        rendered_sections = self.render_sections(template, ctx)

        formats = output_formats or template.default_output_formats
        markdown_text = self.build_markdown(template, rendered_sections) if ReportOutputFormat.MARKDOWN in formats else None
        json_payload = self.build_json_payload(template, rendered_sections) if ReportOutputFormat.JSON in formats else {}

        status = self.classify_report(rendered_sections)

        # Check required sections
        rendered_keys = [s.section_key for s in rendered_sections]
        warnings = []
        for req in template.required_sections:
            if req not in rendered_keys:
                status = ReportValidationStatus.FAIL
                warnings.append(f"Required section missing: {req}")

        return ComposedReport(
            report_id=f"rep_{uuid.uuid4().hex[:8]}",
            template_id=template.template_id,
            template_name=template.name,
            kind=template.kind,
            generated_at=datetime.utcnow(),
            sections=rendered_sections,
            output_formats=formats,
            markdown_text=markdown_text,
            json_payload=json_payload,
            status=status,
            warnings=warnings
        )

    def collect_context(self, kind: ReportTemplateKind) -> Dict[str, Any]:
        return {
            "summary": f"Auto-generated context for {kind.value}",
            "status": "PASS",
            "warnings": []
        }

    def render_sections(self, template: ReportTemplate, context: Dict[str, Any]) -> List[RenderedReportSection]:
        sections = []
        for sec_def in sorted(template.sections, key=lambda x: x.order):
            sec = self.section_library.render_section(sec_def, context)
            sections.append(sec)
        return sections

    def build_markdown(self, template: ReportTemplate, sections: List[RenderedReportSection]) -> str:
        lines = [f"# {template.name.replace('_', ' ').title()}\n"]
        for s in sections:
            lines.append(f"## {s.title}\n")
            lines.append(f"{s.content_markdown}\n")
        return "\n".join(lines)

    def build_json_payload(self, template: ReportTemplate, sections: List[RenderedReportSection]) -> Dict[str, Any]:
        # JSON serializable payload
        payload = {
            "template_name": template.name,
            "sections": {}
        }
        for s in sections:
            try:
                json.dumps(s.content_json) # Test serializability
                payload["sections"][s.section_key] = s.content_json
            except (TypeError, ValueError):
                payload["sections"][s.section_key] = {"error": "Not serializable"}
        return payload

    def classify_report(self, sections: List[RenderedReportSection]) -> ReportValidationStatus:
        statuses = [s.status for s in sections]
        if ReportValidationStatus.FAIL in statuses:
            return ReportValidationStatus.FAIL
        if ReportValidationStatus.WATCH in statuses:
            return ReportValidationStatus.WATCH
        return ReportValidationStatus.PASS
