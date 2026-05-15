from datetime import datetime
from typing import Any, Dict, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_data_dir
# Mock import for now to avoid breaking existing healthcheck tests
from bist_signal_bot.app.quality_app import create_quality_config_from_settings, create_quality_gate_runner

class AppHealthcheck:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()

    def run(self) -> Dict[str, Any]:
        status = {
            "status": "UP",
            "timestamp": datetime.utcnow().isoformat(),
            "data_dir_writable": self._check_data_dir(),
        }

        status["quality"] = self._check_quality()

        return status

    def _check_data_dir(self) -> bool:
        try:
            test_file = get_data_dir(self.settings) / ".healthcheck"
            test_file.touch()
            test_file.unlink()
            return True
        except Exception:
            return False

    def _check_quality(self) -> Dict[str, Any]:
        try:
            config = create_quality_config_from_settings(self.settings)

            # Smoke instantiation
            runner = create_quality_gate_runner(self.settings)

            return {
                "enabled": getattr(self.settings, "ENABLE_QUALITY_GATE", True),
                "default_suite": config.suite.value,
                "gate_level": config.gate_level.value,
                "run_tests": config.run_tests,
                "run_coverage": config.run_coverage,
                "run_static": config.run_static,
                "run_type_check": config.run_type_check,
                "run_import_checks": config.run_import_checks,
                "run_security_checks": config.run_security_checks,
                "run_regression_smoke": config.run_regression_smoke,
                "coverage_threshold": config.coverage_threshold_pct,
                "timeout_seconds": config.timeout_seconds,
                "quality_runner_instantiable": runner is not None,
                "import_check_capable": runner.import_runner is not None,
                "security_quality_check_capable": runner.security_runner is not None,
                "smoke_config_capable": True
            }
        except Exception as e:
            return {
                "enabled": getattr(self.settings, "ENABLE_QUALITY_GATE", True),
                "error": str(e)
            }

def run_healthcheck(settings=None):
    hc = AppHealthcheck(settings=settings)
    return hc.run()
