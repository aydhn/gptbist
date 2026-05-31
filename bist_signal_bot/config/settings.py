from pydantic import BaseModel, Field

class MonitoringSettings(BaseModel):
    # Main
    ENABLE_RESEARCH_MONITORING: bool = True
    MONITORING_DIR_NAME: str = "monitoring"
    MONITORING_RESEARCH_ONLY: bool = True
    MONITORING_SAVE_RESULTS: bool = True

    # Windows
    MONITORING_SHORT_WINDOW: int = 30
    MONITORING_MEDIUM_WINDOW: int = 90
    MONITORING_LONG_WINDOW: int = 252
    MONITORING_MIN_SAMPLE: int = 30

    # Metrics
    MONITORING_ENABLE_WIN_RATE: bool = True
    MONITORING_ENABLE_EXPECTANCY: bool = True
    MONITORING_ENABLE_PROFIT_FACTOR: bool = True
    MONITORING_ENABLE_DRAWDOWN: bool = True
    MONITORING_ENABLE_CALIBRATION_RELIABILITY: bool = True

    # Decay
    MONITORING_DECAY_ENABLED: bool = True
    MONITORING_DECAY_WARN_SCORE: float = 40.0
    MONITORING_DECAY_FAIL_SCORE: float = 70.0
    MONITORING_PERFORMANCE_DECAY_THRESHOLD: float = 0.15
    MONITORING_CALIBRATION_DECAY_THRESHOLD: float = 0.10
    MONITORING_HEALTH_DEGRADED_THRESHOLD: float = 50.0
    MONITORING_HEALTH_WATCH_THRESHOLD: float = 65.0

    # Champion / Challenger
    MONITORING_CHAMPION_CHALLENGER_ENABLED: bool = True
    MONITORING_CHALLENGER_MIN_SAMPLE: int = 50
    MONITORING_CHALLENGER_PROMOTION_MARGIN: float = 5.0
    MONITORING_CHALLENGER_REQUIRES_REVIEW: bool = True

    # Alerts
    MONITORING_ALERTS_ENABLED: bool = True
    MONITORING_AUTO_CREATE_REVIEW_CASES: bool = False
    MONITORING_ROUTE_ALERTS_TO_REVIEW: bool = True
    MONITORING_ROUTE_ALERTS_TO_REPORTS: bool = True
    MONITORING_ACK_REQUIRED_FOR_CRITICAL: bool = True

    # Watchlist
    MONITORING_WATCHLIST_ENABLED: bool = True
    MONITORING_AUTO_WATCH_DEGRADED: bool = True

class Settings(BaseModel):
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)

def get_settings() -> Settings:
    return Settings()
