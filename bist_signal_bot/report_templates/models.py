from enum import Enum
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
