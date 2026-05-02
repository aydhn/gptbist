from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_contains_patterns():
    # Because healthcheck internally creates its own settings in run_healthcheck:
    summary = run_healthcheck()
    settings = Settings()

    assert "pattern_detectors" in summary
    assert summary["pattern_detectors"]["enabled"] == settings.ENABLE_PATTERN_DETECTORS
    assert summary["pattern_detectors"]["feature_level"] == settings.PATTERN_FEATURE_LEVEL
    assert "registered_pattern_detector_count" in summary["pattern_detectors"]
