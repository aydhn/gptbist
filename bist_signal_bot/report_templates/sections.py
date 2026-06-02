import uuid
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from bist_signal_bot.report_templates.models import (
    ReportSectionDefinition, ReportSectionKind, RenderedReportSection, ReportValidationStatus
)

class ReportSectionLibrary:
    def __init__(self, settings=None):
        self.settings = settings
        self._sections = {s.section_key: s for s in self.default_sections()}

    def default_sections(self) -> List[ReportSectionDefinition]:
        return [
            ReportSectionDefinition(
                section_id="sec_summary", section_key="summary", title="Executive Summary",
                kind=ReportSectionKind.SUMMARY, required=True, order=10, renderer_name="render_summary_section"
            ),
            ReportSectionDefinition(
                section_id="sec_warnings", section_key="warnings", title="Warnings & Risk Factors",
                kind=ReportSectionKind.WARNINGS, required=False, order=20, renderer_name="render_warnings_section"
            ),
            ReportSectionDefinition(
                section_id="sec_status", section_key="status_table", title="System Status",
                kind=ReportSectionKind.STATUS_TABLE, required=False, order=30, renderer_name="render_status_table_section"
            ),
            ReportSectionDefinition(
                section_id="sec_disclaimer", section_key="disclaimer", title="Disclaimer",
                kind=ReportSectionKind.DISCLAIMER, required=True, order=999, renderer_name="render_disclaimer_section"
            )
        ]

    def get_section(self, section_key: str) -> Optional[ReportSectionDefinition]:
        return self._sections.get(section_key)

    def sections_for_template_kind(self, kind: str) -> List[ReportSectionDefinition]:
        # Simple implementation for now
        return list(self._sections.values())

    def render_section(self, section: ReportSectionDefinition, context: Dict[str, Any]) -> RenderedReportSection:
        renderer = getattr(self, section.renderer_name, None) if section.renderer_name else None
        if not renderer:
            return RenderedReportSection(
                rendered_section_id=str(uuid.uuid4()),
                section_key=section.section_key,
                title=section.title,
                content_markdown=f"*(Renderer {section.renderer_name} missing)*",
                content_json={"error": "missing_renderer"},
                status=ReportValidationStatus.WATCH,
                warnings=["Renderer missing"]
            )

        try:
            return renderer(context)
        except Exception as e:
            return RenderedReportSection(
                rendered_section_id=str(uuid.uuid4()),
                section_key=section.section_key,
                title=section.title,
                content_markdown=f"*(Error rendering section: {str(e)})*",
                content_json={"error": str(e)},
                status=ReportValidationStatus.FAIL,
                warnings=[f"Render error: {str(e)}"]
            )

    def render_summary_section(self, context: Dict[str, Any]) -> RenderedReportSection:
        summary = context.get("summary", "No summary provided.")
        return RenderedReportSection(
            rendered_section_id=str(uuid.uuid4()),
            section_key="summary",
            title="Executive Summary",
            content_markdown=str(summary),
            content_json={"summary": summary},
            status=ReportValidationStatus.PASS
        )

    def render_warnings_section(self, context: Dict[str, Any]) -> RenderedReportSection:
        warnings = context.get("warnings", [])
        if not warnings:
            md = "No warnings."
        else:
            md = "\n".join([f"- {w}" for w in warnings])
        return RenderedReportSection(
            rendered_section_id=str(uuid.uuid4()),
            section_key="warnings",
            title="Warnings & Risk Factors",
            content_markdown=md,
            content_json={"warnings": warnings},
            status=ReportValidationStatus.PASS
        )

    def render_status_table_section(self, context: Dict[str, Any]) -> RenderedReportSection:
        status = context.get("status", "Unknown")
        return RenderedReportSection(
            rendered_section_id=str(uuid.uuid4()),
            section_key="status_table",
            title="System Status",
            content_markdown=f"Current status: **{status}**",
            content_json={"status": status},
            status=ReportValidationStatus.PASS
        )

    def render_disclaimer_section(self, context: Dict[str, Any]) -> RenderedReportSection:
        disclaimer = context.get("disclaimer", "Report template is local software reporting metadata only. It is not investment advice or permission to trade. No real order was sent.")
        return RenderedReportSection(
            rendered_section_id=str(uuid.uuid4()),
            section_key="disclaimer",
            title="Disclaimer",
            content_markdown=f"> *{disclaimer}*",
            content_json={"disclaimer": disclaimer},
            status=ReportValidationStatus.PASS
        )
