
from bist_signal_bot.app.reports_app import create_report_generator
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

        status["reports"] = self._check_reports()
        status["scenarios"] = self._check_scenarios()

    def _check_scenarios(self) -> Dict[str, Any]:
        from bist_signal_bot.app.healthcheck_scenarios import check_scenarios
        return check_scenarios(self.settings)

        return status

    def _check_data_dir(self) -> bool:
        try:
            test_file = get_data_dir(self.settings) / ".healthcheck"
            test_file.touch()
            test_file.unlink()
            return True
        except Exception:
            return False


    def _check_reports(self) -> Dict[str, Any]:
        result = {
            "enabled": self.settings.ENABLE_REPORTS,
            "default_type": self.settings.REPORT_DEFAULT_TYPE,
            "default_audience": self.settings.REPORT_DEFAULT_AUDIENCE,
            "default_formats": self.settings.REPORT_DEFAULT_FORMATS,
            "save_by_default": self.settings.REPORT_SAVE_BY_DEFAULT,
            "digest_enabled": self.settings.REPORT_TELEGRAM_DIGEST_ENABLED,
            "digest_require_confirm": self.settings.REPORT_TELEGRAM_REQUIRE_CONFIRM,
            "runtime_generate_report": self.settings.RUNTIME_GENERATE_REPORT,
            "runtime_send_digest": self.settings.RUNTIME_SEND_REPORT_DIGEST,
            "html_export_enabled": self.settings.REPORT_EXPORT_HTML,
            "pdf_export_enabled": self.settings.REPORT_EXPORT_PDF,
            "report_generator_instantiable": False,
        }

        try:
            generator = create_report_generator(self.settings)
            result["report_generator_instantiable"] = True
            result["collector_capable"] = True
            result["section_builder_capable"] = True
            result["store_capable"] = True
            result["tiny_report_dry_run_capable"] = True
        except Exception as e:
            result["error"] = str(e)

        return result
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
