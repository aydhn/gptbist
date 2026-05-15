from pathlib import Path
from typing import Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.quality.gate import QualityGateRunner
from bist_signal_bot.quality.models import QualityRunConfig, QualitySuite, QualityGateLevel

def create_quality_gate_runner(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> QualityGateRunner:
    s = settings or Settings()
    return QualityGateRunner(settings=s)

def create_quality_config_from_settings(settings: Settings) -> QualityRunConfig:
    # Safely get attributes that might not exist yet if settings wasn't updated
    suite_str = getattr(settings, "QUALITY_DEFAULT_SUITE", "FAST")
    gate_level_str = getattr(settings, "QUALITY_GATE_LEVEL", "STANDARD")

    try:
        suite = QualitySuite(suite_str)
    except ValueError:
        suite = QualitySuite.FAST

    try:
        gate_level = QualityGateLevel(gate_level_str)
    except ValueError:
        gate_level = QualityGateLevel.STANDARD

    return QualityRunConfig(
        suite=suite,
        gate_level=gate_level,
        run_tests=getattr(settings, "QUALITY_RUN_TESTS", True),
        run_coverage=getattr(settings, "QUALITY_RUN_COVERAGE", False),
        run_static=getattr(settings, "QUALITY_RUN_STATIC", True),
        run_type_check=getattr(settings, "QUALITY_RUN_TYPE_CHECK", False),
        run_import_checks=getattr(settings, "QUALITY_RUN_IMPORT_CHECKS", True),
        run_security_checks=getattr(settings, "QUALITY_RUN_SECURITY_CHECKS", True),
        run_regression_smoke=getattr(settings, "QUALITY_RUN_REGRESSION_SMOKE", False),
        fail_on_warning=getattr(settings, "QUALITY_FAIL_ON_WARNING", False),
        coverage_threshold_pct=getattr(settings, "QUALITY_COVERAGE_THRESHOLD_PCT", 60.0),
        timeout_seconds=getattr(settings, "QUALITY_TIMEOUT_SECONDS", 300),
        save_report=getattr(settings, "QUALITY_SAVE_REPORT", True)
    )

def create_smoke_quality_config(settings: Settings) -> QualityRunConfig:
    config = create_quality_config_from_settings(settings)
    config.suite = QualitySuite.SMOKE
    # In smoke, we might want to run fewer things to keep it fast
    config.run_coverage = False
    config.run_regression_smoke = False
    return config
