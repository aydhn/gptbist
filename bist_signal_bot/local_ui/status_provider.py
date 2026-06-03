from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.local_ui.models import LocalUIStatus

class LocalUIStatusProvider:
    def __init__(self, settings: Settings | None = None, base_dir=None):
        self.settings = settings or get_settings()

    def collect_home_status(self) -> dict:
        return {
            "mode": "RESEARCH",
            "uptime": "unknown",
            "overall_status": LocalUIStatus.PASS.value
        }

    def collect_healthcheck_status(self) -> dict:
        return {"status": LocalUIStatus.WATCH.value, "details": "Healthcheck data stub"}

    def collect_doctor_status(self) -> dict:
        return {"status": LocalUIStatus.WATCH.value, "details": "Doctor data stub"}

    def collect_qa_status(self) -> dict:
        return {"status": LocalUIStatus.WATCH.value, "details": "QA data stub"}

    def collect_ops_status(self) -> dict:
        return {"status": LocalUIStatus.WATCH.value, "details": "Ops data stub"}

    def collect_module_status(self, module_name: str) -> dict:
        return {"status": LocalUIStatus.WATCH.value, "details": f"{module_name} data stub"}

    def collect_latest_reports(self) -> dict:
        return {"reports": []}

    def collect_command_registry(self) -> list:
        return [{"command": "healthcheck"}, {"command": "doctor"}, {"command": "qa"}]
