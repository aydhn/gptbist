import os
import re
from pathlib import Path

# Create directories
os.makedirs("bist_signal_bot/monitoring", exist_ok=True)
os.makedirs("bist_signal_bot/tests", exist_ok=True)
os.makedirs("bist_signal_bot/docs", exist_ok=True)
os.makedirs("bist_signal_bot/examples", exist_ok=True)

# 1. monitoring/models.py
with open("bist_signal_bot/monitoring/models.py", "w") as f:
    f.write('''from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Optional, List, Dict

class MonitoringStatus(str, Enum):
    PASS = "PASS"
    WATCH = "WATCH"
    DEGRADED = "DEGRADED"
    FAIL = "FAIL"
    BLOCKED_RESEARCH = "BLOCKED_RESEARCH"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"

class MonitoringObjectType(str, Enum):
    STRATEGY = "STRATEGY"
    MODEL = "MODEL"
    FEATURE_SET = "FEATURE_SET"
    SIGNAL_FAMILY = "SIGNAL_FAMILY"
    PORTFOLIO_RESEARCH = "PORTFOLIO_RESEARCH"
    CALIBRATION_POLICY = "CALIBRATION_POLICY"
    CONTEXT_LAYER = "CONTEXT_LAYER"
    CUSTOM = "CUSTOM"

class MonitoringWindow(str, Enum):
    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    LONG = "LONG"
    CUSTOM = "CUSTOM"

class DecayType(str, Enum):
    PERFORMANCE_DECAY = "PERFORMANCE_DECAY"
    CALIBRATION_DECAY = "CALIBRATION_DECAY"
    WIN_RATE_DECAY = "WIN_RATE_DECAY"
    EXPECTANCY_DECAY = "EXPECTANCY_DECAY"
    RISK_ADJUSTED_DECAY = "RISK_ADJUSTED_DECAY"
    HIT_RATE_DECAY = "HIT_RATE_DECAY"
    FEATURE_DRIFT_LINKED_DECAY = "FEATURE_DRIFT_LINKED_DECAY"
    MODEL_DRIFT_LINKED_DECAY = "MODEL_DRIFT_LINKED_DECAY"
    SAMPLE_QUALITY_DECAY = "SAMPLE_QUALITY_DECAY"
    UNKNOWN = "UNKNOWN"

class ChampionChallengerDecision(str, Enum):
    KEEP_CHAMPION = "KEEP_CHAMPION"
    WATCH_CHAMPION = "WATCH_CHAMPION"
    PROMOTE_CHALLENGER_RESEARCH = "PROMOTE_CHALLENGER_RESEARCH"
    REJECT_CHALLENGER = "REJECT_CHALLENGER"
    NEEDS_MORE_DATA = "NEEDS_MORE_DATA"
    ESCALATE_REVIEW = "ESCALATE_REVIEW"
    UNKNOWN = "UNKNOWN"

class MonitoringAlertType(str, Enum):
    STRATEGY_DEGRADED = "STRATEGY_DEGRADED"
    MODEL_DEGRADED = "MODEL_DEGRADED"
    CALIBRATION_DECAY = "CALIBRATION_DECAY"
    FEATURE_DRIFT = "FEATURE_DRIFT"
    MODEL_DRIFT = "MODEL_DRIFT"
    LOW_SAMPLE = "LOW_SAMPLE"
    STALE_OUTCOMES = "STALE_OUTCOMES"
    QUALITY_GATE_FAIL = "QUALITY_GATE_FAIL"
    CHAMPION_CHALLENGER_CHANGE = "CHAMPION_CHALLENGER_CHANGE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    CUSTOM = "CUSTOM"

class MonitoringMetric(BaseModel):
    metric_id: str
    object_type: MonitoringObjectType
    object_id: str
    metric_name: str
    window: MonitoringWindow
    value: Optional[float] = None
    baseline_value: Optional[float] = None
    delta: Optional[float] = None
    sample_count: Optional[int] = None
    as_of: datetime
    status: MonitoringStatus
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MonitoringSnapshot(BaseModel):
    snapshot_id: str
    object_type: MonitoringObjectType
    object_id: str
    as_of: datetime
    metrics: List[MonitoringMetric] = Field(default_factory=list)
    status: MonitoringStatus
    health_score: Optional[float] = None
    sample_count: Optional[int] = None
    key_findings: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Monitoring snapshot is local research performance metadata only. It is not investment advice or permission to trade. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PerformanceDecayFinding(BaseModel):
    decay_id: str
    object_type: MonitoringObjectType
    object_id: str
    decay_type: DecayType
    metric_name: str
    baseline_value: Optional[float] = None
    current_value: Optional[float] = None
    decay_score: Optional[float] = None
    status: MonitoringStatus
    message: str
    evidence_refs: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Performance decay finding is research-only metadata. It does not predict future returns or authorize trading. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChampionChallengerComparison(BaseModel):
    comparison_id: str
    object_type: MonitoringObjectType
    champion_id: str
    challenger_id: str
    as_of: datetime
    champion_metrics: List[MonitoringMetric] = Field(default_factory=list)
    challenger_metrics: List[MonitoringMetric] = Field(default_factory=list)
    decision: ChampionChallengerDecision
    decision_score: Optional[float] = None
    reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Champion/challenger comparison is local research governance metadata only. It is not investment advice or live deployment approval. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MonitoringAlert(BaseModel):
    alert_id: str
    alert_type: MonitoringAlertType
    object_type: MonitoringObjectType
    object_id: str
    severity: str
    status: MonitoringStatus
    created_at: datetime
    title: str
    message: str
    evidence_refs: List[str] = Field(default_factory=list)
    routed_to: List[str] = Field(default_factory=list)
    review_case_id: Optional[str] = None
    acknowledged: bool = False
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Monitoring alert is local research review metadata only. It is not a trading alert or order instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MonitoringWatchlistItem(BaseModel):
    watch_id: str
    object_type: MonitoringObjectType
    object_id: str
    added_at: datetime
    reason: str
    status: MonitoringStatus
    latest_snapshot_id: Optional[str] = None
    latest_alert_id: Optional[str] = None
    review_case_id: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MonitoringReport(BaseModel):
    report_id: str
    generated_at: datetime
    snapshots: List[MonitoringSnapshot] = Field(default_factory=list)
    decay_findings: List[PerformanceDecayFinding] = Field(default_factory=list)
    champion_challenger: List[ChampionChallengerComparison] = Field(default_factory=list)
    alerts: List[MonitoringAlert] = Field(default_factory=list)
    watchlist: List[MonitoringWatchlistItem] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Monitoring report is local research monitoring output only. It is not investment advice, portfolio advice, or a trading instruction. No real order was sent."
    metadata: Dict[str, Any] = Field(default_factory=dict)
''')

# 2. Update core/exceptions.py
try:
    with open("bist_signal_bot/core/exceptions.py", "r") as f:
        exceptions_content = f.read()

    new_exceptions = '''
class ResearchMonitoringError(BistSignalBotError):
    """Base exception for research monitoring errors."""
    pass

class MonitoringMetricError(ResearchMonitoringError):
    pass

class MonitoringCollectorError(ResearchMonitoringError):
    pass

class PerformanceDecayError(ResearchMonitoringError):
    pass

class ChampionChallengerError(ResearchMonitoringError):
    pass

class MonitoringHealthError(ResearchMonitoringError):
    pass

class MonitoringAlertError(ResearchMonitoringError):
    pass

class MonitoringEscalationError(ResearchMonitoringError):
    pass

class MonitoringWatchlistError(ResearchMonitoringError):
    pass

class MonitoringStorageError(ResearchMonitoringError):
    pass
'''
    if "ResearchMonitoringError" not in exceptions_content:
        with open("bist_signal_bot/core/exceptions.py", "a") as f:
            f.write(new_exceptions)
except Exception as e:
    print(f"Error updating exceptions: {e}")

# 3. Update core/audit.py
try:
    with open("bist_signal_bot/core/audit.py", "r") as f:
        audit_content = f.read()

    if "MONITORING_METRICS_CALCULATED" not in audit_content:
        audit_content = audit_content.replace(
            "class AuditEventType(str, Enum):",
            "class AuditEventType(str, Enum):\n    MONITORING_METRICS_CALCULATED = 'MONITORING_METRICS_CALCULATED'\n    MONITORING_SNAPSHOT_CREATED = 'MONITORING_SNAPSHOT_CREATED'\n    PERFORMANCE_DECAY_DETECTED = 'PERFORMANCE_DECAY_DETECTED'\n    CHAMPION_CHALLENGER_COMPARED = 'CHAMPION_CHALLENGER_COMPARED'\n    MONITORING_ALERT_CREATED = 'MONITORING_ALERT_CREATED'\n    MONITORING_ALERT_ACKNOWLEDGED = 'MONITORING_ALERT_ACKNOWLEDGED'\n    MONITORING_ESCALATED_TO_REVIEW = 'MONITORING_ESCALATED_TO_REVIEW'\n    MONITORING_WATCHLIST_UPDATED = 'MONITORING_WATCHLIST_UPDATED'\n    MONITORING_REPORT_CREATED = 'MONITORING_REPORT_CREATED'"
        )
        with open("bist_signal_bot/core/audit.py", "w") as f:
            f.write(audit_content)
except Exception as e:
    print(f"Error updating audit: {e}")

# 4. Update config/settings.py
try:
    with open("bist_signal_bot/config/settings.py", "r") as f:
        settings_content = f.read()

    new_settings = '''
    # Monitoring
    ENABLE_RESEARCH_MONITORING: bool = True
    MONITORING_DIR_NAME: str = "monitoring"
    MONITORING_RESEARCH_ONLY: bool = True
    MONITORING_SAVE_RESULTS: bool = True
    MONITORING_SHORT_WINDOW: int = 30
    MONITORING_MEDIUM_WINDOW: int = 90
    MONITORING_LONG_WINDOW: int = 252
    MONITORING_MIN_SAMPLE: int = 30
    MONITORING_ENABLE_WIN_RATE: bool = True
    MONITORING_ENABLE_EXPECTANCY: bool = True
    MONITORING_ENABLE_PROFIT_FACTOR: bool = True
    MONITORING_ENABLE_DRAWDOWN: bool = True
    MONITORING_ENABLE_CALIBRATION_RELIABILITY: bool = True
    MONITORING_DECAY_ENABLED: bool = True
    MONITORING_DECAY_WARN_SCORE: float = 40.0
    MONITORING_DECAY_FAIL_SCORE: float = 70.0
    MONITORING_PERFORMANCE_DECAY_THRESHOLD: float = 0.15
    MONITORING_CALIBRATION_DECAY_THRESHOLD: float = 0.10
    MONITORING_HEALTH_DEGRADED_THRESHOLD: float = 50.0
    MONITORING_HEALTH_WATCH_THRESHOLD: float = 65.0
    MONITORING_CHAMPION_CHALLENGER_ENABLED: bool = True
    MONITORING_CHALLENGER_MIN_SAMPLE: int = 50
    MONITORING_CHALLENGER_PROMOTION_MARGIN: float = 5.0
    MONITORING_CHALLENGER_REQUIRES_REVIEW: bool = True
    MONITORING_ALERTS_ENABLED: bool = True
    MONITORING_AUTO_CREATE_REVIEW_CASES: bool = False
    MONITORING_ROUTE_ALERTS_TO_REVIEW: bool = True
    MONITORING_ROUTE_ALERTS_TO_REPORTS: bool = True
    MONITORING_ACK_REQUIRED_FOR_CRITICAL: bool = True
    MONITORING_WATCHLIST_ENABLED: bool = True
    MONITORING_AUTO_WATCH_DEGRADED: bool = True
    RUNTIME_MONITORING_ENABLED: bool = True
    RUNTIME_MONITORING_WARN_ONLY: bool = True
    QA_INCLUDE_MONITORING: bool = True
    QA_MONITORING_FAIL_ON_BLOCKED_RESEARCH: bool = True
    OPS_INCLUDE_MONITORING: bool = True
    REPORT_INCLUDE_MONITORING: bool = True
    RESEARCH_AUTO_LOG_MONITORING: bool = False
'''
    if "ENABLE_RESEARCH_MONITORING" not in settings_content:
        # insert before class ends or just before last config definition
        # For simplicity, append just before the Settings config class
        settings_content = re.sub(
            r"(class Settings\(BaseSettings\):.*?)(    class Config:)",
            r"\1" + new_settings + r"\n\2",
            settings_content,
            flags=re.DOTALL
        )
        with open("bist_signal_bot/config/settings.py", "w") as f:
            f.write(settings_content)
except Exception as e:
    print(f"Error updating settings: {e}")

# 5. update storage/paths.py
try:
    with open("bist_signal_bot/storage/paths.py", "r") as f:
        paths_content = f.read()

    if "get_monitoring_dir" not in paths_content:
        paths_content += '''
def get_monitoring_dir(settings=None) -> Path:
    from bist_signal_bot.config.settings import get_settings
    if settings is None:
        settings = get_settings()
    data_dir = get_data_dir(settings)
    d = data_dir / settings.MONITORING_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d
'''
        with open("bist_signal_bot/storage/paths.py", "w") as f:
            f.write(paths_content)
except Exception as e:
    print(f"Error updating paths: {e}")

print("Basic setup done.")
