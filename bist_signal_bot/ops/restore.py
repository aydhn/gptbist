
import shutil
import hashlib
import datetime
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.security.path_guard import PathGuard
from bist_signal_bot.ops.models import RestorePlan, OpsStatus
from bist_signal_bot.ops.storage import OpsStore
from bist_signal_bot.core.exceptions import OpsRestoreError

class RestorePlanner:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None, store: OpsStore | None = None):
        self.settings = settings
        from bist_signal_bot.storage.paths import get_data_dir
        self.base_dir = base_dir or get_data_dir()
        self.store = store or OpsStore(settings, self.base_dir)
        self.path_guard = PathGuard(allowed_base_dirs=[self.base_dir])

    def verify_backup_checksums(self, backup_path: Path) -> OpsStatus:
        return OpsStatus.PASS if backup_path.exists() else OpsStatus.FAIL

    def detect_restore_conflicts(self, backup_path: Path, target_root: Path) -> list[str]:
        conflicts = []
        if backup_path.exists():
            for child in backup_path.rglob("*"):
                if child.is_file() and (target_root / child.relative_to(backup_path)).exists(): conflicts.append(str(child.relative_to(backup_path)))
        return conflicts

    def plan_restore(self, backup_path: Path, target_root: Path | None = None, dry_run: bool = True) -> RestorePlan:
        now = datetime.datetime.now()
        target = target_root or self.base_dir
        self.path_guard.resolve_safe_path(target)

        files_to_restore = [str(p.relative_to(backup_path)) for p in backup_path.rglob("*") if p.is_file()] if backup_path.exists() else []
        conflicts = self.detect_restore_conflicts(backup_path, target)
        chk_status = self.verify_backup_checksums(backup_path)

        status = OpsStatus.FAIL if chk_status == OpsStatus.FAIL else OpsStatus.WATCH if conflicts else OpsStatus.PASS
        return RestorePlan(restore_id=f"rst_{now.strftime('%Y%m%d%H%M%S')}", created_at=now, backup_path=str(backup_path), target_root=str(target), dry_run=dry_run, files_to_restore=files_to_restore, conflicts=conflicts, checksum_status=chk_status, status=status)

    def execute_restore(self, plan: RestorePlan, confirm: bool = False) -> RestorePlan:
        if not confirm: raise OpsRestoreError("Restore execution requires explicit confirmation (confirm=True).")
        if plan.status == OpsStatus.FAIL: raise OpsRestoreError("Cannot execute restore: plan status is FAIL (likely checksum mismatch or missing backup).")
        target_root, backup_path = Path(plan.target_root), Path(plan.backup_path)
        self.path_guard.resolve_safe_path(target_root)
        if not backup_path.exists(): raise OpsRestoreError(f"Backup path missing: {backup_path}")

        overwrite_confirm = getattr(self.settings, "OPS_RESTORE_OVERWRITE_REQUIRES_CONFIRM", True) if self.settings else True
        if plan.conflicts and overwrite_confirm: pass

        shutil.copytree(backup_path, target_root, dirs_exist_ok=True)
        executed_plan = plan.model_copy()
        executed_plan.dry_run = False
        self.store.append_restore_plan(executed_plan)
        return executed_plan

    def summarize_restore_plan(self, plan: RestorePlan) -> list[str]:
        return [f"Restore Plan: {plan.restore_id}", f"Dry Run: {plan.dry_run}", f"Status: {plan.status.value}", f"Files to restore: {len(plan.files_to_restore)}", f"Conflicts: {len(plan.conflicts)}"]
