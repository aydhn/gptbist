import uuid
from datetime import datetime, timezone
from pathlib import Path
from bist_signal_bot.maintenance_automation.models import BackupManifest, MaintenanceStatus

class BackupManifestBuilder:
    def default_backup_paths(self) -> list[Path]:
        return [Path("data")]

    def checksum_paths(self, paths: list[Path]) -> dict[str, str]:
        return {str(p): "mock_hash_123" for p in paths}

    def build_backup_manifest(self, source_paths: list[Path] = None, dry_run: bool = True) -> BackupManifest:
        paths = source_paths or self.default_backup_paths()
        paths_str = [str(p) for p in paths]
        return BackupManifest(
            backup_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            source_paths=paths_str,
            checksum_manifest=self.checksum_paths(paths),
            dry_run=dry_run,
            status=MaintenanceStatus.PASS
        )

    def validate_backup_manifest(self, manifest: BackupManifest) -> list[str]:
        errors = []
        if not manifest.source_paths:
            errors.append("No source paths specified.")
        return errors

    def backup_summary(self, manifest: BackupManifest) -> dict:
        return {
            "id": manifest.backup_id,
            "status": manifest.status,
            "paths_count": len(manifest.source_paths)
        }
