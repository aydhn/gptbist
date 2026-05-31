import re

with open("bist_signal_bot/config/settings.py", "r") as f:
    content = f.read()

new_settings = """
    # Monitoring Settings
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
"""

if "MONITORING_HEALTH_DEGRADED_THRESHOLD" not in content:
    content = re.sub(
        r"(class Settings\(BaseSettings\):.*?)(    model_config = SettingsConfigDict)",
        r"\1" + new_settings + r"\n\2",
        content,
        flags=re.DOTALL
    )
    with open("bist_signal_bot/config/settings.py", "w") as f:
        f.write(content)
