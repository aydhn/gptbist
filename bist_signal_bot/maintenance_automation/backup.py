import uuid
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timezone
import hashlib
from bist_signal_bot.maintenance_automation.models import BackupManifest, MaintenanceStatus

class BackupManifestBuilder:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def default_backup_paths(self) -> List[Path]:
        return [
            self.base_dir / "data" / "reports",
            self.base_dir / "data" / "config",
            self.base_dir / "data" / "research"
        ]

    def checksum_paths(self, paths: List[Path]) -> Dict[str, str]:
        manifest = {}
        for path in paths:
            if path.is_file():
                try:
                    with open(path, 'rb') as f:
                        file_hash = hashlib.sha256()
                        while chunk := f.read(8192):
                            file_hash.update(chunk)
                    manifest[str(path)] = file_hash.hexdigest()
                except Exception:
                    pass
        return manifest

    def build_backup_manifest(self, source_paths: Optional[List[Path]] = None, dry_run: bool = True) -> BackupManifest:
        if source_paths is None:
            source_paths = self.default_backup_paths()

        all_files = []
        for path in source_paths:
            if path.is_file():
                all_files.append(path)
            elif path.is_dir():
                all_files.extend([p for p in path.rglob("*") if p.is_file()])

        checksums = self.checksum_paths(all_files)
        str_paths = [str(p) for p in source_paths]

        manifest = BackupManifest(
            backup_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            source_paths=str_paths,
            checksum_manifest=checksums,
            dry_run=dry_run,
            status=MaintenanceStatus.PASS
        )
        return manifest

    def validate_backup_manifest(self, manifest: BackupManifest) -> List[str]:
        errors = []
        if not manifest.disclaimer or "not investment advice" not in manifest.disclaimer.lower() or "broker backup" not in manifest.disclaimer.lower():
            errors.append("Disclaimer must clearly state it is not investment advice or broker backup.")
        return errors

    def backup_summary(self, manifest: BackupManifest) -> Dict[str, Any]:
        return {
            "backup_id": manifest.backup_id,
            "source_path_count": len(manifest.source_paths),
            "file_count": len(manifest.checksum_manifest),
            "dry_run": manifest.dry_run,
            "status": manifest.status.value
        }
