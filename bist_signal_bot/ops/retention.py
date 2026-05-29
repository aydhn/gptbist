
import datetime
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.ops.models import RetentionFinding, RetentionAction, OpsStatus
from bist_signal_bot.ops.storage import OpsStore
from bist_signal_bot.core.exceptions import OpsRetentionError

class RetentionPolicyEngine:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None, store: OpsStore | None = None):
        self.settings = settings
        from bist_signal_bot.storage.paths import get_data_dir
        self.base_dir = base_dir or get_data_dir()
        self.store = store or OpsStore(settings, self.base_dir)

    def policy_for_module(self, module_name: str) -> dict[str, Any]:
        return {
            "archive_days": getattr(self.settings, f"OPS_ARCHIVE_OLD_{module_name.upper()}_DAYS", 180),
            "keep_raw": getattr(self.settings, "OPS_KEEP_RAW_RESEARCH_DATA", True)
        }

    def classify_file(self, path: Path) -> tuple[str | None, RetentionAction, str]:
        module = "REPORTS" if "reports" in str(path) else "UNKNOWN"
        now = datetime.datetime.now()
        age_days = (now - datetime.datetime.fromtimestamp(path.stat().st_mtime)).days
        policy = self.policy_for_module(module)
        if age_days > policy["archive_days"]: return module, RetentionAction.ARCHIVE, f"Exceeds {policy['archive_days']} days."
        return module, RetentionAction.KEEP, "Within retention period."

    def analyze_retention(self, root: Path | None = None, dry_run: bool = True) -> list[RetentionFinding]:
        target = root or self.base_dir
        findings = []
        now = datetime.datetime.now()
        if target.exists() and target.is_dir():
            for p in target.rglob("*"):
                if p.is_file():
                    mod, action, reason = self.classify_file(p)
                    if action != RetentionAction.KEEP:
                        age = (now - datetime.datetime.fromtimestamp(p.stat().st_mtime)).days
                        findings.append(RetentionFinding(
                            finding_id=f"ret_{now.timestamp()}", path=str(p), module_name=mod, age_days=age, size_bytes=p.stat().st_size,
                            action=action if not dry_run else RetentionAction.DELETE_DRY_RUN if action == RetentionAction.DELETE_CONFIRMED else action,
                            dry_run=dry_run, reason=reason, status=OpsStatus.PASS
                        ))
        return findings

    def archive_candidates(self, findings: list[RetentionFinding]) -> list[RetentionFinding]:
        return [f for f in findings if f.action == RetentionAction.ARCHIVE]

    def apply_retention(self, findings: list[RetentionFinding], confirm: bool = False) -> list[RetentionFinding]:
        if not confirm: raise OpsRetentionError("Applying retention requires explicit confirmation (confirm=True).")
        applied = []
        for f in findings:
            p = Path(f.path)
            if f.action == RetentionAction.ARCHIVE:
                archive_dir = self.base_dir / "archive"
                archive_dir.mkdir(parents=True, exist_ok=True)
                dest = archive_dir / p.name
                if p.exists():
                    try:
                        p.rename(dest)
                        f.dry_run = False
                        f.status = OpsStatus.PASS
                        applied.append(f)
                    except Exception as e:
                        f.status = OpsStatus.FAIL
                        f.warnings.append(str(e))
                        applied.append(f)
        if applied: self.store.append_retention_findings(applied)
        return applied
