import json
from enum import Enum
from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field

class ReportType(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    RUNTIME_SUMMARY = "RUNTIME_SUMMARY"
    SCANNER_SUMMARY = "SCANNER_SUMMARY"
    RESEARCH_SUMMARY = "RESEARCH_SUMMARY"
    PAPER_SUMMARY = "PAPER_SUMMARY"
    OPERATIONS_SUMMARY = "OPERATIONS_SUMMARY"
    CUSTOM = "CUSTOM"

class ReportStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
    EMPTY = "EMPTY"
    SKIPPED = "SKIPPED"

class ReportOutputFormat(str, Enum):
    MARKDOWN = "MARKDOWN"
    JSON = "JSON"
    CSV = "CSV"
    HTML = "HTML"
    PDF = "PDF"
    TEXT = "TEXT"

class ReportSectionType(str, Enum):
    DISCLAIMER = "DISCLAIMER"
    EXECUTIVE_SUMMARY = "EXECUTIVE_SUMMARY"
    MARKET_REGIME = "MARKET_REGIME"
    SCANNER_HIGHLIGHTS = "SCANNER_HIGHLIGHTS"
    RISK_SUMMARY = "RISK_SUMMARY"
    PORTFOLIO_RISK = "PORTFOLIO_RISK"
    ML_SUMMARY = "ML_SUMMARY"
    ADAPTIVE_SUMMARY = "ADAPTIVE_SUMMARY"
    PAPER_SUMMARY = "PAPER_SUMMARY"
    BACKTEST_SUMMARY = "BACKTEST_SUMMARY"
    OPTIMIZATION_SUMMARY = "OPTIMIZATION_SUMMARY"
    RESEARCH_LEDGER = "RESEARCH_LEDGER"
    SIGNAL_JOURNAL = "SIGNAL_JOURNAL"
    ATTRIBUTION = "ATTRIBUTION"
    RUNTIME_OPERATIONS = "RUNTIME_OPERATIONS"
    MONITORING = "MONITORING"
    SECURITY = "SECURITY"
    QUALITY = "QUALITY"
    PERFORMANCE = "PERFORMANCE"
    APPENDIX = "APPENDIX"
    CUSTOM = "CUSTOM"

class ReportAudience(str, Enum):
    PERSONAL = "PERSONAL"
    INTERNAL_RESEARCH = "INTERNAL_RESEARCH"
    TECHNICAL = "TECHNICAL"
    EXECUTIVE = "EXECUTIVE"
    TELEGRAM_DIGEST = "TELEGRAM_DIGEST"

class ReportDataSource(str, Enum):
    RESEARCH_LEDGER = "RESEARCH_LEDGER"
    SIGNAL_JOURNAL = "SIGNAL_JOURNAL"
    SCANNER = "SCANNER"
    BACKTEST = "BACKTEST"
    OPTIMIZATION = "OPTIMIZATION"
    PAPER = "PAPER"
    ML = "ML"
    REGIME = "REGIME"
    ADAPTIVE = "ADAPTIVE"
    RUNTIME = "RUNTIME"
    MONITORING = "MONITORING"
    SECURITY = "SECURITY"
    QUALITY = "QUALITY"
    PERFORMANCE = "PERFORMANCE"
    MANUAL = "MANUAL"
    UNKNOWN = "UNKNOWN"

class ReportSection(BaseModel):
    section_id: str
    section_type: ReportSectionType
    title: str
    body_markdown: str
    summary: dict[str, Any] = Field(default_factory=dict)
    tables: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    charts: dict[str, Any] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if not self.title.strip():
            raise ValueError("title cannot be empty")

class ReportConfig(BaseModel):
    report_type: ReportType = ReportType.DAILY
    audience: ReportAudience = ReportAudience.PERSONAL
    formats: list[ReportOutputFormat] = Field(default_factory=lambda: [ReportOutputFormat.MARKDOWN, ReportOutputFormat.JSON, ReportOutputFormat.CSV])
    include_sections: list[ReportSectionType] = Field(default_factory=list)
    exclude_sections: list[ReportSectionType] = Field(default_factory=list)
    start_date: datetime | None = None
    end_date: datetime | None = None
    symbols: list[str] = Field(default_factory=list)
    strategies: list[str] = Field(default_factory=list)
    top_n: int = 10
    include_empty_sections: bool = False
    send_telegram: bool = False
    save_report: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        if self.top_n <= 0:
            raise ValueError("top_n must be positive")
        if not self.formats:
            raise ValueError("formats cannot be empty")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date cannot be greater than end_date")
        self.symbols = [s.upper() for s in self.symbols]

class ReportDataBundle(BaseModel):
    report_type: ReportType
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    source_summaries: dict[str, Any] = Field(default_factory=dict)
    scanner_items: list[dict[str, Any]] = Field(default_factory=list)
    journal_items: list[dict[str, Any]] = Field(default_factory=list)
    research_runs: list[dict[str, Any]] = Field(default_factory=list)
    paper_items: list[dict[str, Any]] = Field(default_factory=list)
    regime_items: list[dict[str, Any]] = Field(default_factory=list)
    ml_items: list[dict[str, Any]] = Field(default_factory=list)
    adaptive_items: list[dict[str, Any]] = Field(default_factory=list)
    monitoring_items: list[dict[str, Any]] = Field(default_factory=list)
    quality_items: list[dict[str, Any]] = Field(default_factory=list)
    security_items: list[dict[str, Any]] = Field(default_factory=list)
    performance_items: list[dict[str, Any]] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class GeneratedReport(BaseModel):
    report_id: str
    report_type: ReportType
    audience: ReportAudience
    status: ReportStatus
    title: str
    sections: list[ReportSection] = Field(default_factory=list)
    data_bundle_summary: dict[str, Any] = Field(default_factory=dict)
    output_files: dict[str, str] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    elapsed_seconds: float = 0.0
    disclaimer: str = "Research report output only. Not investment advice. No real order was sent."
    warnings: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "report_type": self.report_type.value,
            "status": self.status.value,
            "title": self.title,
            "section_count": len(self.sections),
            "generated_at": self.generated_at.isoformat()
        }
    def safe_public_dict(self) -> dict[str, Any]:
        # Serialize with model_dump using JSON mode to handle datetimes
        return json.loads(self.model_dump_json())

class TelegramDigest(BaseModel):
    digest_id: str
    report_id: str | None = None
    title: str
    message: str
    top_items: list[dict[str, Any]] = Field(default_factory=list)
    status: ReportStatus = ReportStatus.EMPTY
    sent: bool = False
    sent_at: datetime | None = None
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Telegram digest is research-only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
