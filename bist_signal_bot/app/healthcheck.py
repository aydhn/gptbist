import logging
from typing import Dict, Any
from bist_signal_bot.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

class HealthChecker:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def run(self) -> Dict[str, Any]:
        logger.info("Running healthcheck...")
        status = {
            "status": "OK",
            "components": {
                "config": "OK",
                "storage": "OK",
                "drift_monitoring": "OK" if self.settings.ENABLE_DRIFT_MONITORING else "DISABLED",
                "research_lab": "OK" if getattr(self.settings, "ENABLE_RESEARCH_LAB", True) else "DISABLED"
            }
        }
        return status

def run_healthcheck(settings: Settings | None = None) -> Dict[str, Any]:
    checker = HealthChecker(settings)
    return checker.run()
