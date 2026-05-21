import zipfile
import tarfile
import shutil
import time
from pathlib import Path
from bist_signal_bot.maintenance.models import (
    BackupRequest,
    BackupResult,
    BackupFormat,
    MaintenanceStatus,
    BackupFileEntry
)
from bist_signal_bot.maintenance.manifest import BackupManifestBuilder
from bist_signal_bot.maintenance.checksum import ChecksumManager
from bist_signal_bot.core.exceptions import BackupError
from bist_signal_bot.config.settings import get_settings

class BackupManager:
    def __init__(self, base_dir: Path, output_dir: Path):
        self.base_dir = base_dir
        self.output_dir = output_dir
        self.settings = get_settings()

    def create_backup(self, request: BackupRequest) -> BackupResult:
        start_time = time.time()
        warnings = []
        errors = []

        try:
            # 1. Scan files
            entries = BackupManifestBuilder.scan_files_for_scope(self.base_dir, request.scopes)

            # 2. Check for secret risk
            for entry in entries:
                if entry.included:
                    is_excluded, reason = BackupManifestBuilder.should_exclude(Path(entry.relative_path))
                    if is_excluded:
                        entry.included = False
                        entry.excluded_reason = reason
                        warnings.append(f"Excluded file during preflight: {entry.relative_path} ({reason})")

            # 3. Calculate checksums
            entries = ChecksumManager.checksum_manifest_entries(entries, self.base_dir)

            archive_path = None
            if not request.dry_run:
                # 4. Create archive
                self.output_dir.mkdir(parents=True, exist_ok=True)
                timestamp = time.strftime("%Y%m%d%H%M%S")

                if request.backup_format == BackupFormat.ZIP:
                    archive_path = self.output_dir / f"backup_{timestamp}.zip"
                    self.create_zip_backup(entries, self.base_dir, archive_path)
                elif request.backup_format == BackupFormat.TAR_GZ:
                    archive_path = self.output_dir / f"backup_{timestamp}.tar.gz"
                    self.create_tar_gz_backup(entries, self.base_dir, archive_path)
                elif request.backup_format == BackupFormat.DIRECTORY_COPY:
                    archive_path = self.output_dir / f"backup_{timestamp}"
                    self.create_directory_copy(entries, self.base_dir, archive_path)

            # 5. Build manifest
            manifest = BackupManifestBuilder.build_manifest(request, self.base_dir, entries, archive_path)

            if not request.dry_run:
                BackupManifestBuilder.write_manifest(manifest, self.output_dir)

            verified = False
            if not request.dry_run and request.verify_after_create:
                verify_errors = BackupManifestBuilder.verify_manifest(manifest, self.base_dir, archive_path)
                if verify_errors:
                    errors.extend(verify_errors)
                    warnings.append("Backup verification failed")
                else:
                    verified = True

            status = MaintenanceStatus.SUCCESS
            if errors:
                status = MaintenanceStatus.FAILED
            elif warnings:
                status = MaintenanceStatus.PARTIAL_SUCCESS

            if request.dry_run:
                 status = MaintenanceStatus.SUCCESS # Or something else

            return BackupResult(
                backup_id=manifest.backup_id,
                request=request,
                status=status,
                manifest=manifest,
                output_path=str(archive_path) if archive_path else None,
                verified=verified,
                elapsed_seconds=time.time() - start_time,
                warnings=warnings,
                errors=errors
            )

        except Exception as e:
            return BackupResult(
                backup_id="failed",
                request=request,
                status=MaintenanceStatus.FAILED,
                manifest=BackupManifestBuilder.build_manifest(request, self.base_dir, []), # Empty manifest
                elapsed_seconds=time.time() - start_time,
                errors=[str(e)]
            )

    def create_zip_backup(self, files: list[BackupFileEntry], base_dir: Path, output_path: Path) -> Path:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for entry in files:
                if entry.included:
                    file_path = base_dir / entry.relative_path
                    zipf.write(file_path, arcname=entry.relative_path)
        return output_path

    def create_tar_gz_backup(self, files: list[BackupFileEntry], base_dir: Path, output_path: Path) -> Path:
        with tarfile.open(output_path, "w:gz") as tar:
             for entry in files:
                if entry.included:
                    file_path = base_dir / entry.relative_path
                    tar.add(file_path, arcname=entry.relative_path)
        return output_path

    def create_directory_copy(self, files: list[BackupFileEntry], base_dir: Path, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        for entry in files:
             if entry.included:
                 src_path = base_dir / entry.relative_path
                 dst_path = output_dir / entry.relative_path
                 dst_path.parent.mkdir(parents=True, exist_ok=True)
                 shutil.copy2(src_path, dst_path)
        return output_dir
