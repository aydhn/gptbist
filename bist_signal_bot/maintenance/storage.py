import json
from pathlib import Path
from typing import Any
from datetime import datetime, timezone
from bist_signal_bot.maintenance.models import (
    BackupResult,
    RestoreResult,
    CleanupResult,
    MigrationResult,
    MaintenanceDoctorReport
)
from bist_signal_bot.config.settings import get_settings

class MaintenanceStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.settings = get_settings()
        self.maintenance_dir = self.base_dir / getattr(self.settings, "MAINTENANCE_DIR_NAME", "maintenance")
        self.backup_dir = self.maintenance_dir / getattr(self.settings, "BACKUP_DIR_NAME", "backups")
        self.manifests_dir = self.maintenance_dir / "manifests"
        self.restore_dir = self.maintenance_dir / "restore"
        self.cleanup_dir = self.maintenance_dir / "cleanup"
        self.migrations_dir = self.maintenance_dir / "migrations"
        self.doctor_dir = self.maintenance_dir / "doctor"
        self.policies_dir = self.maintenance_dir / "policies"

        self._ensure_dirs()

    def _ensure_dirs(self):
        for d in [self.maintenance_dir, self.backup_dir, self.manifests_dir,
                  self.restore_dir, self.cleanup_dir, self.migrations_dir,
                  self.doctor_dir, self.policies_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def get_maintenance_dir(self) -> Path:
        return self.maintenance_dir

    def get_backup_dir(self) -> Path:
        return self.backup_dir

    def _get_date_dir(self, base: Path) -> Path:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        return base / date_str

    def save_backup_result(self, result: BackupResult) -> dict[str, Path]:
        date_dir = self._get_date_dir(self.backup_dir)
        op_dir = date_dir / result.backup_id
        op_dir.mkdir(parents=True, exist_ok=True)

        res_path = op_dir / "backup_result.json"
        with open(res_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))

        manifest_path = self.manifests_dir / f"{result.backup_id}_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(result.manifest.model_dump_json(indent=2))

        self._append_operation("BACKUP_CREATE", result.backup_id, result.status.value, str(res_path))
        return {"result": res_path, "manifest": manifest_path}

    def save_restore_result(self, result: RestoreResult) -> dict[str, Path]:
        date_dir = self._get_date_dir(self.restore_dir)
        op_dir = date_dir / result.restore_id
        op_dir.mkdir(parents=True, exist_ok=True)

        res_path = op_dir / "restore_result.json"
        with open(res_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))

        self._append_operation("RESTORE", result.restore_id, result.status.value, str(res_path))
        return {"result": res_path}

    def save_cleanup_result(self, result: CleanupResult) -> dict[str, Path]:
        date_dir = self._get_date_dir(self.cleanup_dir)
        op_dir = date_dir / result.cleanup_id
        op_dir.mkdir(parents=True, exist_ok=True)

        res_path = op_dir / "cleanup_result.json"
        with open(res_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))

        self._append_operation("CLEANUP", result.cleanup_id, result.status.value, str(res_path))
        return {"result": res_path}

    def save_migration_result(self, result: MigrationResult) -> dict[str, Path]:
        history_path = self.migrations_dir / "migration_history.jsonl"

        with open(history_path, "a", encoding="utf-8") as f:
            f.write(result.model_dump_json() + "\n")

        self._append_operation("MIGRATION", result.migration_id, result.status.value, str(history_path))
        return {"result": history_path}

    def save_doctor_report(self, report: MaintenanceDoctorReport) -> dict[str, Path]:
        date_dir = self._get_date_dir(self.doctor_dir)
        op_dir = date_dir / report.report_id
        op_dir.mkdir(parents=True, exist_ok=True)

        res_path = op_dir / "doctor_report.json"
        with open(res_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

        self._append_operation("DOCTOR", report.report_id, report.status.value, str(res_path))
        return {"result": res_path}

    def _append_operation(self, op_type: str, op_id: str, status: str, path: str):
        ops_path = self.maintenance_dir / "operations.jsonl"
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": op_type,
            "id": op_id,
            "status": status,
            "path": path
        }
        with open(ops_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def list_backups(self, limit: int = 20) -> list[dict[str, Any]]:
        backups = []
        for p in sorted(self.manifests_dir.glob("*_manifest.json"), reverse=True):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    backups.append({
                        "backup_id": data.get("backup_id"),
                        "created_at": data.get("created_at"),
                        "format": data.get("backup_format"),
                        "size_bytes": data.get("total_size_bytes"),
                        "archive_path": data.get("archive_path")
                    })
                    if len(backups) >= limit:
                        break
            except Exception:
                continue
        return backups

    def list_operations(self, limit: int = 20) -> list[dict[str, Any]]:
        ops_path = self.maintenance_dir / "operations.jsonl"
        ops = []
        if ops_path.exists():
            try:
                with open(ops_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in reversed(lines):
                        if not line.strip():
                            continue
                        ops.append(json.loads(line))
                        if len(ops) >= limit:
                            break
            except Exception:
                pass
        return ops
