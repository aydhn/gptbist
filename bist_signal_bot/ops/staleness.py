
import datetime
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_data_dir
from bist_signal_bot.ops.models import StalenessFinding, OpsStatus, OpsSeverity

class StalenessChecker:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir or get_data_dir()

    def threshold_for_module(self, module_name: str) -> int:
        return getattr(self.settings, f"OPS_STALE_{module_name.upper()}_DAYS", 7) if self.settings else 7

    def last_modified(self, path: Path) -> datetime.datetime | None:
        if not path.exists(): return None
        latest = None
        if path.is_dir():
            for p in path.rglob("*"):
                if p.is_file():
                    mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime)
                    if latest is None or mtime > latest: latest = mtime
        else: latest = datetime.datetime.fromtimestamp(path.stat().st_mtime)
        return latest

    def classify_staleness(self, age_days: int | None, threshold_days: int) -> tuple[OpsStatus, OpsSeverity]:
        if age_days is None: return OpsStatus.INSUFFICIENT_DATA, OpsSeverity.INFO
        if age_days > threshold_days: return OpsStatus.WATCH, OpsSeverity.MEDIUM
        return OpsStatus.PASS, OpsSeverity.INFO

    def check_module(self, module_name: str, expected_path: Path, threshold_days: int) -> StalenessFinding:
        now = datetime.datetime.now()
        last_mod = self.last_modified(expected_path)
        age_days = (now - last_mod).days if last_mod else None

        status, severity = self.classify_staleness(age_days, threshold_days)
        msg = f"{module_name} is fresh."
        if status == OpsStatus.WATCH: msg = f"{module_name} data is stale ({age_days} days > {threshold_days} threshold)."
        elif status == OpsStatus.INSUFFICIENT_DATA: msg = f"No data found for {module_name}."

        return StalenessFinding(
            finding_id=f"stale_{module_name}_{now.timestamp()}", module_name=module_name,
            object_type="directory", object_id=str(expected_path), last_updated_at=last_mod,
            stale_days=age_days, threshold_days=threshold_days, status=status, severity=severity, message=msg
        )

    def check_all(self) -> list[StalenessFinding]:
        modules = [("data", self.base_dir / "data"), ("macro", self.base_dir / "macro"), ("breadth", self.base_dir / "breadth")]
        return [self.check_module(mod_name, path, self.threshold_for_module(mod_name)) for mod_name, path in modules]
