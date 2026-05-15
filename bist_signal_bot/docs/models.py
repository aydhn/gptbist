from enum import Enum
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator

class DocsPageType(str, Enum):
    OVERVIEW = "OVERVIEW"
    QUICKSTART = "QUICKSTART"
    INSTALLATION = "INSTALLATION"
    CONFIGURATION = "CONFIGURATION"
    COMMAND_CATALOG = "COMMAND_CATALOG"
    MODULE_GUIDE = "MODULE_GUIDE"
    RUNBOOK = "RUNBOOK"
    TROUBLESHOOTING = "TROUBLESHOOTING"
    FAQ = "FAQ"
    ARCHITECTURE = "ARCHITECTURE"
    GLOSSARY = "GLOSSARY"
    DEVELOPER_GUIDE = "DEVELOPER_GUIDE"
    TEMPLATE = "TEMPLATE"
    UNKNOWN = "UNKNOWN"

class DocsValidationStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"

class DocsOutputFormat(str, Enum):
    MARKDOWN = "MARKDOWN"
    JSON = "JSON"
    CSV = "CSV"
    TEXT = "TEXT"

class CommandRiskLevel(str, Enum):
    SAFE = "SAFE"
    PAPER_ONLY = "PAPER_ONLY"
    FILE_WRITING = "FILE_WRITING"
    LONG_RUNNING = "LONG_RUNNING"
    DESTRUCTIVE_REQUIRES_CONFIRM = "DESTRUCTIVE_REQUIRES_CONFIRM"
    UNKNOWN = "UNKNOWN"

class DocsPage(BaseModel):
    path: str
    title: str
    page_type: DocsPageType
    description: str
    required_sections: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    generated: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("path", "title")
    @classmethod
    def not_empty(cls, v):
        if not v:
            raise ValueError("cannot be empty")
        return v

class CLICommandDoc(BaseModel):
    command: str
    description: str
    examples: list[str] = Field(default_factory=list)
    risk_level: CommandRiskLevel
    requires_network: bool
    sends_telegram: bool
    writes_files: bool
    requires_confirm: bool
    no_real_order_sent: bool
    module: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("command")
    @classmethod
    def command_not_empty(cls, v):
        if not v:
            raise ValueError("command cannot be empty")
        return v

    @field_validator("no_real_order_sent")
    @classmethod
    def must_be_true(cls, v):
        if not v:
            raise ValueError("no_real_order_sent must be true")
        return v

class RunbookStep(BaseModel):
    step_number: int
    title: str
    command: Optional[str] = None
    expected_result: str
    if_failed: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class Runbook(BaseModel):
    runbook_id: str
    title: str
    symptom: str
    severity: str
    affected_components: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    steps: list[RunbookStep] = Field(default_factory=list)
    rollback_steps: list[RunbookStep] = Field(default_factory=list)
    escalation_notes: list[str] = Field(default_factory=list)
    disclaimer: str = "Operational runbook only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class TroubleshootingItem(BaseModel):
    problem: str
    likely_causes: list[str] = Field(default_factory=list)
    diagnostic_commands: list[str] = Field(default_factory=list)
    fix_steps: list[str] = Field(default_factory=list)
    prevention: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DocsValidationFinding(BaseModel):
    path: str
    status: DocsValidationStatus
    severity: str
    message: str
    line_number: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class DocsValidationReport(BaseModel):
    status: DocsValidationStatus = DocsValidationStatus.PASS
    checked_files: int = 0
    findings: list[DocsValidationFinding] = Field(default_factory=list)
    command_examples_checked: int = 0
    unsafe_claims_found: int = 0
    secrets_found: int = 0
    missing_pages: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    disclaimer: str = "Documentation validation output only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "checked_files": self.checked_files,
            "findings": len(self.findings),
            "unsafe_claims_found": self.unsafe_claims_found,
            "secrets_found": self.secrets_found,
            "missing_pages": len(self.missing_pages),
            "command_examples_checked": self.command_examples_checked,
        }

class DocsGenerationResult(BaseModel):
    status: DocsValidationStatus = DocsValidationStatus.PASS
    pages_created: int = 0
    pages_updated: int = 0
    output_files: dict[str, str] = Field(default_factory=dict)
    validation_report: Optional[DocsValidationReport] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime = Field(default_factory=datetime.utcnow)
    elapsed_seconds: float = 0.0
    disclaimer: str = "Documentation generation output only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "pages_created": self.pages_created,
            "pages_updated": self.pages_updated,
            "elapsed_seconds": self.elapsed_seconds,
            "disclaimer": self.disclaimer
        }
