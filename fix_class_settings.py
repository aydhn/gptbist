import re

with open("bist_signal_bot/config/settings.py", "r") as f:
    content = f.read()

settings_fields = """
    # Drift Settings (Phase 58)
    ENABLE_DRIFT_MONITORING: bool = True
    DRIFT_DIR_NAME: str = "drift"
    DRIFT_SAVE_RESULTS: bool = True
    DRIFT_DEFAULT_DOMAINS: str = "FEATURE,MODEL_SCORE,SIGNAL_OUTCOME,STRATEGY_PERFORMANCE,PORTFOLIO_RESEARCH"
    DRIFT_MIN_SAMPLES: int = 30
    DRIFT_REFERENCE_WINDOW_TYPE: str = "LAST_N_DAYS"
    DRIFT_REFERENCE_DAYS: int = 90
    DRIFT_CURRENT_DAYS: int = 14
    DRIFT_REFERENCE_UPDATE_REQUIRES_CONFIRM: bool = True
    DRIFT_FEATURE_PSI_WARN: float = 0.10
    DRIFT_FEATURE_PSI_FAIL: float = 0.25
    DRIFT_FEATURE_PSI_SEVERE: float = 0.50
    DRIFT_FEATURE_KS_WARN: float = 0.20
    DRIFT_FEATURE_KS_FAIL: float = 0.35
    DRIFT_MODEL_SCORE_PSI_WARN: float = 0.10
    DRIFT_MODEL_SCORE_PSI_FAIL: float = 0.25
    DRIFT_MODEL_POSITIVE_RATE_CHANGE_WARN: float = 25.0
    DRIFT_MODEL_POSITIVE_RATE_CHANGE_FAIL: float = 50.0
    DRIFT_CALIBRATION_ENABLED: bool = True
    DRIFT_CALIBRATION_BINS: int = 10
    DRIFT_ECE_WARN: float = 0.08
    DRIFT_ECE_FAIL: float = 0.15
    DRIFT_BRIER_WARN: float = 0.25
    DRIFT_SIGNAL_DECAY_ENABLED: bool = True
    DRIFT_SIGNAL_OUTCOME_DROP_WARN: float = 20.0
    DRIFT_SIGNAL_OUTCOME_DROP_FAIL: float = 40.0
    DRIFT_MUTED_ALERT_RATE_WARN: float = 50.0
    DRIFT_INVALIDATION_RATE_WARN: float = 35.0
    DRIFT_STRATEGY_DECAY_ENABLED: bool = True
    DRIFT_STRATEGY_DECAY_SCORE_WARN: float = 40.0
    DRIFT_STRATEGY_DECAY_SCORE_FAIL: float = 70.0
    DRIFT_PORTFOLIO_DRIFT_ENABLED: bool = True
    DRIFT_EXPOSURE_CHANGE_WARN: float = 0.20
    DRIFT_CONCENTRATION_CHANGE_WARN: float = 0.15
    DRIFT_CORRELATION_CHANGE_WARN: float = 0.20
    RUNTIME_RUN_DRIFT_CHECK: bool = False
    RESEARCH_AUTO_LOG_DRIFT: bool = False

    def check_drift_settings(self) -> 'Settings':
        return self
"""

# Insert inside class Settings before def check_research_settings
content = content.replace("    def check_research_settings(self) -> 'Settings':", settings_fields + "\n    def check_research_settings(self) -> 'Settings':")

with open("bist_signal_bot/config/settings.py", "w") as f:
    f.write(content)
