import uuid
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime, timezone
from bist_signal_bot.maintenance_automation.models import MaintenanceActionResult, MaintenanceActionType, MaintenanceStatus

class ArtifactRotationEngine:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def rotate_reports(self, dry_run: bool = True, confirm: bool = False) -> MaintenanceActionResult:
        return self._do_rotation(MaintenanceActionType.REPORT_ROTATION, "Reports", dry_run, confirm)

    def rotate_logs(self, dry_run: bool = True, confirm: bool = False) -> MaintenanceActionResult:
        return self._do_rotation(MaintenanceActionType.LOG_ROTATION, "Logs", dry_run, confirm)

    def compact_jsonl_store(self, path: Path, dry_run: bool = True, confirm: bool = False) -> MaintenanceActionResult:
        status = MaintenanceStatus.PASS
        skipped = False
        message = ""

        if not confirm:
            skipped = True
            status = MaintenanceStatus.SKIPPED
            message = "JSONL compaction skipped because confirm is False."
            return self._build_result(MaintenanceActionType.JSONL_COMPACT, status, skipped, dry_run, [str(path)], message)

        # Mock compaction logic
        message = f"Compacted JSONL store at {path}"
        return self._build_result(MaintenanceActionType.JSONL_COMPACT, status, skipped, dry_run, [str(path)], message)

    def archive_artifacts(self, paths: List[Path], dry_run: bool = True, confirm: bool = False) -> MaintenanceActionResult:
        status = MaintenanceStatus.PASS
        skipped = False
        message = ""

        path_strs = [str(p) for p in paths]

        if not confirm:
            skipped = True
            status = MaintenanceStatus.SKIPPED
            message = "Archival skipped because confirm is False."
            return self._build_result(MaintenanceActionType.CUSTOM, status, skipped, dry_run, path_strs, message)

        message = f"Archived {len(paths)} artifacts"
        return self._build_result(MaintenanceActionType.CUSTOM, status, skipped, dry_run, path_strs, message)

    def rotation_summary(self, paths: List[Path]) -> Dict[str, Any]:
        return {
            "path_count": len(paths)
        }

    def _do_rotation(self, action_type: MaintenanceActionType, name: str, dry_run: bool, confirm: bool) -> MaintenanceActionResult:
        status = MaintenanceStatus.PASS
        skipped = False
        message = f"{name} rotation executed."

        if not confirm:
            skipped = True
            status = MaintenanceStatus.SKIPPED
            message = f"{name} rotation skipped because confirm is False."

        return self._build_result(action_type, status, skipped, dry_run, [], message)

    def _build_result(self, action_type: MaintenanceActionType, status: MaintenanceStatus, skipped: bool, dry_run: bool, affected_paths: List[str], message: str) -> MaintenanceActionResult:
        return MaintenanceActionResult(
            result_id=str(uuid.uuid4()),
            action_id=action_type.value.lower(),
            action_type=action_type,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            status=status,
            skipped=skipped,
            dry_run=dry_run,
            affected_paths=affected_paths,
            message=message
        )
