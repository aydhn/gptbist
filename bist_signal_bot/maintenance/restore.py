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

    def restore(self, request: RestoreRequest, confirm: bool = False) -> RestoreResult:
        start_time = time.time()
        warnings = []
        errors = []
        restored = 0
        skipped = 0
        blocked = 0
        pre_restore_backup_id = None

        try:
            backup_path = Path(request.backup_path)
            if not backup_path.exists():
                raise RestoreError(f"Backup not found: {backup_path}")

            target_dir = Path(request.target_dir) if request.target_dir else self.base_dir

            # Since we only have the archive file usually, we expect the manifest to be next to it
            # or extract it from the archive if we stored it there. Let's assume there is a manifest JSON
            # with the same base name, or we can't do a full scope-based dry run easily.
            # MVP: Just extract directly if no manifest
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

            if not request.dry_run and not confirm:
                raise RestoreValidationError("Restore is destructive. 'confirm' must be True to proceed.")

            if not request.dry_run and request.create_pre_restore_backup:
                pre_req = BackupRequest(scopes=[BackupScope.ALL_SAFE], dry_run=False, verify_after_create=False)
                pre_res = self.backup_manager.create_backup(pre_req)
                if pre_res.status == MaintenanceStatus.SUCCESS:
                     pre_restore_backup_id = pre_res.backup_id
                else:
                     raise RestoreError(f"Pre-restore backup failed: {pre_res.errors}")

            if not request.dry_run:
                if str(backup_path).endswith('.zip'):
                    restored, skipped, blocked, extract_errors = self.restore_zip(backup_path, target_dir, request)
                elif str(backup_path).endswith('.tar.gz'):
                    restored, skipped, blocked, extract_errors = self.restore_tar_gz(backup_path, target_dir, request)
                else: # Assuming directory copy
                    restored, skipped, blocked, extract_errors = self.restore_directory_copy(backup_path, target_dir, request)

                errors.extend(extract_errors)

            status = MaintenanceStatus.SUCCESS
            if errors:
                status = MaintenanceStatus.FAILED if not restored else MaintenanceStatus.PARTIAL_SUCCESS
            elif warnings or blocked > 0:
                status = MaintenanceStatus.PARTIAL_SUCCESS

            if request.dry_run:
                status = MaintenanceStatus.SUCCESS

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
