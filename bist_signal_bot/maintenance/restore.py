import json
import zipfile
import tarfile
import shutil
import time
from pathlib import Path
from bist_signal_bot.maintenance.models import (
    RestoreRequest,
    RestoreResult,
    MaintenanceStatus,
    BackupManifest,
    BackupFormat,
    BackupRequest,
    BackupScope
)
from bist_signal_bot.maintenance.manifest import BackupManifestBuilder
from bist_signal_bot.maintenance.backup import BackupManager
from bist_signal_bot.core.exceptions import RestoreError, RestoreValidationError

class RestoreManager:
    def __init__(self, base_dir: Path, backup_manager: BackupManager):
        self.base_dir = base_dir
        self.backup_manager = backup_manager

    def validate_restore_plan(self, manifest: BackupManifest, request: RestoreRequest) -> list[str]:
        errors = []
        for entry in manifest.file_entries:
            if not entry.included:
                continue

            if entry.scope not in request.scopes and BackupScope.ALL_SAFE not in request.scopes:
                continue

            path = Path(entry.relative_path)

            if '..' in path.parts or path.is_absolute():
                errors.append(f"Path traversal risk detected in backup entry: {entry.relative_path}")

            is_excluded, reason = BackupManifestBuilder.should_exclude(path)
            if is_excluded:
                errors.append(f"Refusing to restore excluded/secret file: {entry.relative_path} ({reason})")

        return errors

    def _load_and_validate_manifest(self, backup_path: Path, request: RestoreRequest, warnings: list) -> None:
        manifest_path = backup_path.with_name(f"{backup_path.stem.replace('backup_', '')}_manifest.json")
        if not manifest_path.exists():
            manifest_path = backup_path.with_name(f"{backup_path.name.split('.')[0].replace('backup_', '')}_manifest.json")

        if manifest_path.exists():
            manifest = BackupManifestBuilder.load_manifest(manifest_path)

            if request.verify_before_restore:
                 verify_errors = BackupManifestBuilder.verify_manifest(manifest, archive_path=backup_path)
                 if verify_errors:
                     raise RestoreValidationError(f"Backup verification failed: {verify_errors}")

            plan_errors = self.validate_restore_plan(manifest, request)
            if plan_errors:
                 raise RestoreValidationError(f"Restore plan validation failed: {plan_errors}")
        else:
             warnings.append("No manifest found. Scope filtering and full validation skipped.")

    def _create_pre_restore_backup(self) -> str:
        pre_req = BackupRequest(scopes=[BackupScope.ALL_SAFE], dry_run=False, verify_after_create=False)
        pre_res = self.backup_manager.create_backup(pre_req)
        if pre_res.status == MaintenanceStatus.SUCCESS:
             return pre_res.backup_id
        raise RestoreError(f"Pre-restore backup failed: {pre_res.errors}")

    def _extract_backup(self, backup_path: Path, target_dir: Path, request: RestoreRequest):
        if str(backup_path).endswith('.zip'):
            return self.restore_zip(backup_path, target_dir, request)
        if str(backup_path).endswith('.tar.gz'):
            return self.restore_tar_gz(backup_path, target_dir, request)
        return self.restore_directory_copy(backup_path, target_dir, request)

    def _determine_status(self, errors: list, warnings: list, restored: int, blocked: int, dry_run: bool) -> MaintenanceStatus:
        if dry_run:
            return MaintenanceStatus.SUCCESS
        if errors:
            return MaintenanceStatus.FAILED if not restored else MaintenanceStatus.PARTIAL_SUCCESS
        if warnings or blocked > 0:
            return MaintenanceStatus.PARTIAL_SUCCESS
        return MaintenanceStatus.SUCCESS

    def restore(self, request: RestoreRequest, confirm: bool = False) -> RestoreResult:
        start_time = time.time()
        warnings = []
        errors = []
        restored = skipped = blocked = 0
        pre_restore_backup_id = None

        try:
            backup_path = Path(request.backup_path)
            if not backup_path.exists():
                raise RestoreError(f"Backup not found: {backup_path}")

            target_dir = Path(request.target_dir) if request.target_dir else self.base_dir

            self._load_and_validate_manifest(backup_path, request, warnings)

            if not request.dry_run and not confirm:
                raise RestoreValidationError("Restore is destructive. 'confirm' must be True to proceed.")

            if not request.dry_run and request.create_pre_restore_backup:
                pre_restore_backup_id = self._create_pre_restore_backup()

            if not request.dry_run:
                restored, skipped, blocked, extract_errors = self._extract_backup(backup_path, target_dir, request)
                errors.extend(extract_errors)

            status = self._determine_status(errors, warnings, restored, blocked, request.dry_run)

            return RestoreResult(
                restore_id=f"rst_{int(time.time())}",
                request=request,
                status=status,
                restored_files=restored,
                skipped_files=skipped,
                blocked_files=blocked,
                pre_restore_backup_id=pre_restore_backup_id,
                warnings=warnings,
                errors=errors,
                elapsed_seconds=time.time() - start_time
            )

        except Exception as e:
            return RestoreResult(
                restore_id=f"rst_{int(time.time())}",
                request=request,
                status=MaintenanceStatus.FAILED,
                elapsed_seconds=time.time() - start_time,
                errors=[str(e)]
            )

    def restore_zip(self, backup_path: Path, target_dir: Path, request: RestoreRequest):
        restored = 0
        skipped = 0
        blocked = 0
        errors = []

        with zipfile.ZipFile(backup_path, 'r') as zf:
             for name in zf.namelist():
                  path = Path(name)
                  if '..' in path.parts or path.is_absolute():
                       blocked += 1
                       errors.append(f"Blocked path traversal risk: {name}")
                       continue
                  is_excluded, reason = BackupManifestBuilder.should_exclude(path)
                  if is_excluded:
                       blocked += 1
                       errors.append(f"Blocked secret/excluded file restore: {name} ({reason})")
                       continue

                  target_path = target_dir / name
                  if target_path.exists() and not request.overwrite:
                       skipped += 1
                       continue

                  target_path.parent.mkdir(parents=True, exist_ok=True)
                  with zf.open(name) as source, open(target_path, "wb") as target:
                       shutil.copyfileobj(source, target)
                  restored += 1
        return restored, skipped, blocked, errors

    def restore_tar_gz(self, backup_path: Path, target_dir: Path, request: RestoreRequest):
        restored = 0
        skipped = 0
        blocked = 0
        errors = []

        with tarfile.open(backup_path, 'r:gz') as tar:
             for member in tar.getmembers():
                  if not member.isfile():
                       continue
                  name = member.name
                  path = Path(name)
                  if '..' in path.parts or path.is_absolute():
                       blocked += 1
                       errors.append(f"Blocked path traversal risk: {name}")
                       continue
                  is_excluded, reason = BackupManifestBuilder.should_exclude(path)
                  if is_excluded:
                       blocked += 1
                       errors.append(f"Blocked secret/excluded file restore: {name} ({reason})")
                       continue

                  target_path = target_dir / name
                  if target_path.exists() and not request.overwrite:
                       skipped += 1
                       continue

                  target_path.parent.mkdir(parents=True, exist_ok=True)
                  f = tar.extractfile(member)
                  if f:
                      with open(target_path, "wb") as target:
                           shutil.copyfileobj(f, target)
                      restored += 1
        return restored, skipped, blocked, errors

    def restore_directory_copy(self, backup_path: Path, target_dir: Path, request: RestoreRequest):
        restored = 0
        skipped = 0
        blocked = 0
        errors = []

        for path in backup_path.rglob('*'):
             if not path.is_file():
                  continue

             rel_path = path.relative_to(backup_path)
             if '..' in rel_path.parts or rel_path.is_absolute():
                  blocked += 1
                  errors.append(f"Blocked path traversal risk: {rel_path}")
                  continue

             is_excluded, reason = BackupManifestBuilder.should_exclude(rel_path)
             if is_excluded:
                  blocked += 1
                  errors.append(f"Blocked secret/excluded file restore: {rel_path} ({reason})")
                  continue

             target_path = target_dir / rel_path
             if target_path.exists() and not request.overwrite:
                  skipped += 1
                  continue

             target_path.parent.mkdir(parents=True, exist_ok=True)
             shutil.copy2(path, target_path)
             restored += 1

        return restored, skipped, blocked, errors
