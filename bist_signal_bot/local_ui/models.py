from enum import Enum
from typing import Any
from datetime import datetime
from pydantic import BaseModel, Field

class LocalUIStatus(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    PASS = "PASS"
    WATCH = "WATCH"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    FALLBACK = "FALLBACK"
    UNKNOWN = "UNKNOWN"

class LocalUIBackend(str, Enum):
    PLAIN_TEXT = "PLAIN_TEXT"
    RICH = "RICH"
    TEXTUAL = "TEXTUAL"
    CURSES = "CURSES"
    AUTO = "AUTO"
    UNKNOWN = "UNKNOWN"

class LocalUIPageKind(str, Enum):
    HOME = "HOME"
    HEALTHCHECK = "HEALTHCHECK"
    DOCTOR = "DOCTOR"
    QA = "QA"
    OPS = "OPS"
    REPORTS = "REPORTS"
    ORCHESTRATOR = "ORCHESTRATOR"
    DATA_CATALOG = "DATA_CATALOG"
    FEATURE_STORE = "FEATURE_STORE"
    MODEL_REGISTRY = "MODEL_REGISTRY"
    MONITORING = "MONITORING"
    LEADERBOARD = "LEADERBOARD"
    FINAL_AUDIT = "FINAL_AUDIT"
    FINAL_HANDOFF = "FINAL_HANDOFF"
    PERFORMANCE = "PERFORMANCE"
    DATA_IMPORT = "DATA_IMPORT"
    SYNTHETIC_SCENARIOS = "SYNTHETIC_SCENARIOS"
    REPORT_TEMPLATES = "REPORT_TEMPLATES"
    COMMANDS = "COMMANDS"
    CONFIG = "CONFIG"
    HELP = "HELP"
    CUSTOM = "CUSTOM"

class LocalUIWidgetKind(str, Enum):
    STATUS_CARD = "STATUS_CARD"
    TABLE = "TABLE"
    KEY_VALUE = "KEY_VALUE"
    WARNING_LIST = "WARNING_LIST"
    COMMAND_LIST = "COMMAND_LIST"
    TEXT_BLOCK = "TEXT_BLOCK"
    NAV_MENU = "NAV_MENU"
    LOG_PREVIEW = "LOG_PREVIEW"
    REPORT_PREVIEW = "REPORT_PREVIEW"
    CUSTOM = "CUSTOM"

class LocalUIActionKind(str, Enum):
    VIEW_ONLY = "VIEW_ONLY"
    DRY_RUN_COMMAND = "DRY_RUN_COMMAND"
    OPEN_REPORT = "OPEN_REPORT"
    SHOW_HELP = "SHOW_HELP"
    REFRESH_STATUS = "REFRESH_STATUS"
    COPY_COMMAND_TEXT = "COPY_COMMAND_TEXT"
    BLOCKED_WRITE_ACTION = "BLOCKED_WRITE_ACTION"
    CUSTOM = "CUSTOM"

class LocalUICapability(BaseModel):
    capability_id: str
    backend: LocalUIBackend
    available: bool
    dependency_name: str | None = None
    version: str | None = None
    status: LocalUIStatus = LocalUIStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class LocalUIWidget(BaseModel):
    widget_id: str
    kind: LocalUIWidgetKind
    title: str
    content: dict[str, Any]
    status: LocalUIStatus = LocalUIStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class LocalUIPage(BaseModel):
    page_id: str
    page_kind: LocalUIPageKind
    title: str
    widgets: list[LocalUIWidget] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    status: LocalUIStatus = LocalUIStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Local UI page displays local research software metadata only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class LocalUILayout(BaseModel):
    layout_id: str
    name: str
    backend: LocalUIBackend
    pages: list[LocalUIPage] = Field(default_factory=list)
    navigation_order: list[str] = Field(default_factory=list)
    default_page: str
    status: LocalUIStatus = LocalUIStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Local UI layout is local terminal navigation metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class LocalUIShortcut(BaseModel):
    shortcut_id: str
    label: str
    command: str
    action_kind: LocalUIActionKind
    dry_run: bool
    requires_confirm: bool
    allowed_in_tui: bool
    audience: str
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Local UI shortcut is local command guidance only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class LocalUIRunResult(BaseModel):
    run_id: str
    backend: LocalUIBackend
    started_at: datetime
    finished_at: datetime | None = None
    status: LocalUIStatus = LocalUIStatus.UNKNOWN
    selected_page: str | None = None
    rendered_pages: list[str] = Field(default_factory=list)
    shortcut_results: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    disclaimer: str = "Local UI run result is local terminal session metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class LocalUIReport(BaseModel):
    report_id: str
    generated_at: datetime
    capabilities: list[LocalUICapability] = Field(default_factory=list)
    layout: LocalUILayout | None = None
    pages: list[LocalUIPage] = Field(default_factory=list)
    shortcuts: list[LocalUIShortcut] = Field(default_factory=list)
    latest_run: LocalUIRunResult | None = None
    key_findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Local UI report is local console governance output only. It is not investment advice or permission to trade. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
