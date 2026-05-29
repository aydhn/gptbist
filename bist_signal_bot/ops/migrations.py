
import datetime
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.ops.models import MigrationCheckResult, OpsStatus
from bist_signal_bot.ops.storage import OpsStore

class MigrationChecker:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None, store: OpsStore | None = None):
        self.settings = settings
        from bist_signal_bot.storage.paths import get_data_dir
        self.base_dir = base_dir or get_data_dir()
        self.store = store or OpsStore(settings, self.base_dir)
        self.schema_version = getattr(settings, "OPS_SCHEMA_VERSION", "1.0") if settings else "1.0"

    def module_schema_versions(self) -> dict[str, str | None]:
        return {"data": "1.0", "macro": "1.0", "breadth": "0.9"}

    def expected_schema_versions(self) -> dict[str, str]:
        return {"data": self.schema_version, "macro": self.schema_version, "breadth": self.schema_version}

    def detect_incompatible_items(self) -> list[str]:
        actual = self.module_schema_versions()
        expected = self.expected_schema_versions()
        return [f"{mod}: actual={ver}, expected={expected.get(mod)}" for mod, ver in actual.items() if expected.get(mod) != ver]

    def migration_required_modules(self) -> list[str]:
        actual = self.module_schema_versions()
        expected = self.expected_schema_versions()
        return [mod for mod, ver in actual.items() if expected.get(mod) != ver]

    def check_migrations(self) -> MigrationCheckResult:
        now = datetime.datetime.now()
        incompat = self.detect_incompatible_items()
        req_mods = self.migration_required_modules()
        status = OpsStatus.WATCH if incompat else OpsStatus.PASS
        res = MigrationCheckResult(
            migration_id=f"mig_{now.strftime('%Y%m%d%H%M%S')}", created_at=now, current_schema_version=self.schema_version,
            expected_schema_version=self.schema_version, modules_checked=list(self.expected_schema_versions().keys()),
            migrations_required=req_mods, incompatible_items=incompat, status=status
        )
        self.store.append_migration_check(res)
        return res
