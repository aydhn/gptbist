import os
from pathlib import Path

os.makedirs("bist_signal_bot/report_templates", exist_ok=True)

with open("bist_signal_bot/report_templates/__init__.py", "w") as f:
    f.write("")

# 1. models.py
with open("bist_signal_bot/report_templates/models.py", "w") as f:
    f.write('''from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Optional, List, Dict

class ReportTemplateStatus(str, Enum):
    ACTIVE = "ACTIVE"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    DRAFT = "DRAFT"
    DEPRECATED = "DEPRECATED"
    UNKNOWN = "UNKNOWN"

class ReportTemplateKind(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    OPERATOR = "OPERATOR"
    DEVELOPER = "DEVELOPER"
    FINAL_AUDIT = "FINAL_AUDIT"
    FINAL_HANDOFF = "FINAL_HANDOFF"
    DATA_QUALITY = "DATA_QUALITY"
    FEATURE_QUALITY = "FEATURE_QUALITY"
    MODEL_GOVERNANCE = "MODEL_GOVERNANCE"
    MONITORING = "MONITORING"
    LEADERBOARD = "LEADERBOARD"
    ORCHESTRATOR = "ORCHESTRATOR"
    PERFORMANCE = "PERFORMANCE"
    DATA_IMPORT = "DATA_IMPORT"
    CUSTOM = "CUSTOM"

class ReportOutputFormat(str, Enum):
    MARKDOWN = "MARKDOWN"
    JSON = "JSON"
    TEXT = "TEXT"
    HTML_DISABLED = "HTML_DISABLED"
    PDF_DISABLED = "PDF_DISABLED"
    CUSTOM = "CUSTOM"

class ReportSectionKind(str, Enum):
    SUMMARY = "SUMMARY"
    STATUS_TABLE = "STATUS_TABLE"
    KEY_FINDINGS = "KEY_FINDINGS"
    WARNINGS = "WARNINGS"
    RISKS = "RISKS"
    ACTION_ITEMS = "ACTION_ITEMS"
    MODULE_STATUS = "MODULE_STATUS"
    DATA_QUALITY = "DATA_QUALITY"
    FEATURE_QUALITY = "FEATURE_QUALITY"
    MODEL_GOVERNANCE = "MODEL_GOVERNANCE"
    MONITORING = "MONITORING"
    LEADERBOARD = "LEADERBOARD"
    ORCHESTRATOR = "ORCHESTRATOR"
    PERFORMANCE = "PERFORMANCE"
    DATA_IMPORT = "DATA_IMPORT"
    QA_OPS = "QA_OPS"
    FINAL_AUDIT = "FINAL_AUDIT"
    FINAL_HANDOFF = "FINAL_HANDOFF"
    APPENDIX = "APPENDIX"
    DISCLAIMER = "DISCLAIMER"
    CUSTOM = "CUSTOM"

class ReportValidationStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"
    UNKNOWN = "UNKNOWN"

class ReportSectionDefinition(BaseModel):
    section_id: str
    section_key: str
    title: str
    kind: ReportSectionKind
    required: bool = False
    order: int
    source_module: Optional[str] = None
    renderer_name: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReportTemplate(BaseModel):
    template_id: str
    name: str
    kind: ReportTemplateKind
    version: str
    description: str
    sections: List[ReportSectionDefinition] = Field(default_factory=list)
    default_output_formats: List[ReportOutputFormat] = Field(default_factory=list)
    required_sections: List[str] = Field(default_factory=list)
    optional_sections: List[str] = Field(default_factory=list)
    status: ReportTemplateStatus = ReportTemplateStatus.ACTIVE
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Report template is local software reporting metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RenderedReportSection(BaseModel):
    rendered_section_id: str
    section_key: str
    title: str
    content_markdown: str
    content_json: Dict[str, Any] = Field(default_factory=dict)
    status: ReportValidationStatus = ReportValidationStatus.UNKNOWN
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ComposedReport(BaseModel):
    report_id: str
    template_id: str
    template_name: str
    kind: ReportTemplateKind
    generated_at: datetime
    sections: List[RenderedReportSection] = Field(default_factory=list)
    output_formats: List[ReportOutputFormat] = Field(default_factory=list)
    markdown_text: Optional[str] = None
    json_payload: Dict[str, Any] = Field(default_factory=dict)
    status: ReportValidationStatus = ReportValidationStatus.UNKNOWN
    key_findings: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Composed report is local research software output only. It is not investment advice, portfolio advice, or a trading instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReportNarrativeBlock(BaseModel):
    block_id: str
    title: str
    text: str
    source_refs: List[str] = Field(default_factory=list)
    safe_language_status: ReportValidationStatus = ReportValidationStatus.UNKNOWN
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Narrative block is local report commentary only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReportExportArtifact(BaseModel):
    artifact_id: str
    report_id: str
    output_format: ReportOutputFormat
    path: str
    created_at: datetime
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    status: ReportValidationStatus = ReportValidationStatus.UNKNOWN
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReportExportPack(BaseModel):
    pack_id: str
    report_id: str
    created_at: datetime
    artifacts: List[ReportExportArtifact] = Field(default_factory=list)
    manifest_id: Optional[str] = None
    status: ReportValidationStatus = ReportValidationStatus.UNKNOWN
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Report export pack contains local report artifacts only. It is not investment advice or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReportManifest(BaseModel):
    manifest_id: str
    report_id: str
    template_id: str
    created_at: datetime
    source_refs: Dict[str, Any] = Field(default_factory=dict)
    artifact_refs: Dict[str, str] = Field(default_factory=dict)
    checksum_manifest: Dict[str, str] = Field(default_factory=dict)
    section_statuses: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Report manifest describes local report generation artifacts only. It is not investment advice or trading approval. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReportTemplateValidationResult(BaseModel):
    validation_id: str
    template_id: Optional[str] = None
    report_id: Optional[str] = None
    created_at: datetime
    status: ReportValidationStatus = ReportValidationStatus.UNKNOWN
    findings: List[str] = Field(default_factory=list)
    unsafe_language_findings: List[str] = Field(default_factory=list)
    missing_required_sections: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Report templates report is local reporting governance output only. It is not investment advice or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReportTemplatesReport(BaseModel):
    report_id: str
    generated_at: datetime
    templates: List[ReportTemplate] = Field(default_factory=list)
    composed_reports: List[ComposedReport] = Field(default_factory=list)
    export_packs: List[ReportExportPack] = Field(default_factory=list)
    manifests: List[ReportManifest] = Field(default_factory=list)
    validations: List[ReportTemplateValidationResult] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Report templates report is local reporting governance output only. It is not investment advice or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)
''')

# 2. sections.py
with open("bist_signal_bot/report_templates/sections.py", "w") as f:
    f.write('''import uuid
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
            md = "\\n".join([f"- {w}" for w in warnings])
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
''')

# 3. library.py
with open("bist_signal_bot/report_templates/library.py", "w") as f:
    f.write('''import uuid
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
''')

# 4. composer.py
with open("bist_signal_bot/report_templates/composer.py", "w") as f:
    f.write('''import uuid
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
        lines = [f"# {template.name.replace('_', ' ').title()}\\n"]
        for s in sections:
            lines.append(f"## {s.title}\\n")
            lines.append(f"{s.content_markdown}\\n")
        return "\\n".join(lines)

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
''')

# 5. narrative.py
with open("bist_signal_bot/report_templates/narrative.py", "w") as f:
    f.write('''import uuid
from typing import List, Optional
from bist_signal_bot.report_templates.models import ReportNarrativeBlock, ReportValidationStatus

class ReportNarrativeGuard:
    def __init__(self, settings=None):
        self.settings = settings
        self.unsafe_keywords = [
            "al", "sat", "kesin al", "kesin sat", "hedef fiyat", "trade ready",
            "işlem yapılabilir", "yatırım tavsiyesidir", "canlı işlem için hazır",
            "guaranteed return", "live deployment approved"
        ]

    def build_narrative_block(self, title: str, text: str, source_refs: Optional[List[str]] = None) -> ReportNarrativeBlock:
        safe_status = ReportValidationStatus.PASS
        warnings = []
        unsafe = self.detect_unsafe_language(text)

        if unsafe:
            safe_status = ReportValidationStatus.BLOCKED
            warnings.append(f"Unsafe language detected: {', '.join(unsafe)}")
            if getattr(self.settings, 'REPORT_NARRATIVE_REWRITE_UNSAFE_SUMMARY', True):
                text = self.rewrite_to_safe_summary(text)
                warnings.append("Text was automatically rewritten to safe summary.")

        return ReportNarrativeBlock(
            block_id=f"nar_{uuid.uuid4().hex[:8]}",
            title=title,
            text=text,
            source_refs=source_refs or [],
            safe_language_status=safe_status,
            warnings=warnings
        )

    def safe_text(self, text: str) -> str:
        unsafe = self.detect_unsafe_language(text)
        if unsafe:
            return self.rewrite_to_safe_summary(text)
        return text

    def detect_unsafe_language(self, text: str) -> List[str]:
        text_lower = text.lower()
        findings = []
        for kw in self.unsafe_keywords:
            if kw in text_lower:
                findings.append(kw)
        return findings

    def validate_narrative(self, block: ReportNarrativeBlock) -> List[str]:
        return block.warnings

    def rewrite_to_safe_summary(self, text: str) -> str:
        # Simple deterministic rewrite rule
        return "[REDACTED] This text contained unsafe language and was rewritten. This is local research metadata only."
''')

print("Phase 103 Part 1 files created.")
