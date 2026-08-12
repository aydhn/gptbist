
import shutil
import hashlib
import datetime
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.security.path_guard import PathGuard
from bist_signal_bot.ops.models import BackupManifest, BackupScope, OpsStatus
from bist_signal_bot.ops.storage import OpsStore

class BackupManager:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None, store: OpsStore | None = None):
        self.settings = settings
        from bist_signal_bot.storage.paths import get_data_dir
        self.base_dir = base_dir or get_data_dir()
        self.store = store or OpsStore(settings, self.base_dir)
        self.path_guard = PathGuard(allowed_base_dirs=[self.base_dir])
        self.backup_root = self.base_dir / "ops" / (getattr(self.settings, "OPS_BACKUP_DIR_NAME", "backups") if self.settings else "backups")

    def resolve_scope_paths(self, scopes: list[BackupScope]) -> list[Path]:
        paths = []
        if BackupScope.ALL in scopes or BackupScope.DATA in scopes:
            p = self.base_dir / "data"
            if p.exists():
                paths.append(p)
            else:
                paths.append(self.base_dir)
        return paths

    def copy_paths(self, paths: list[Path], backup_dir: Path) -> list[Path]:
        copied = []
        for p in paths:
            dest = backup_dir / p.name
            if p.is_dir():
                shutil.copytree(p, dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".env", "*.key", "*token*", "ops"))
                for child in dest.rglob("*"):
                    if child.is_file():
                        copied.append(child)
            elif p.is_file() and not any(x in p.name for x in [".env", "token", ".key"]):
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest)
                copied.append(dest)
        return copied

    def _hash_file_worker(self, p: Path) -> tuple[str, str] | None:
        try:
            if p.is_file():
                with open(p, "rb") as f:
                    # Using file_digest which handles efficient chunking in C
                    return str(p), hashlib.file_digest(f, "sha256").hexdigest()
        except Exception:
            pass
        return None

    def build_checksum_manifest(self, paths: list[Path]) -> dict[str, str]:
        import concurrent.futures
        manifest = {}
        # Parallelize I/O bounds for hashing files
        with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
            for result in executor.map(self._hash_file_worker, paths):
                if result:
                    manifest[result[0]] = result[1]
        return manifest

    def create_backup(self, scopes: list[BackupScope] | None = None, output_dir: Path | None = None, confirm: bool = False) -> BackupManifest:
        now = datetime.datetime.now()
        scopes = scopes or [BackupScope.DATA]
        target_dir = output_dir or (self.backup_root / f"backup_{now.strftime('%Y%m%d%H%M%S')}")

        if not confirm:
            return BackupManifest(backup_id=f"dry_bkp_{now.strftime('%Y%m%d%H%M%S')}", created_at=now, scope=scopes, source_root=str(self.base_dir), backup_path=str(target_dir), status=OpsStatus.WATCH, warnings=["Dry-run: backup not created. Requires confirm=True."])

        self.path_guard.resolve_safe_path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        copied_files = self.copy_paths(self.resolve_scope_paths(scopes), target_dir)

        manifest = BackupManifest(
            backup_id=f"bkp_{now.strftime('%Y%m%d%H%M%S')}", created_at=now, scope=scopes, source_root=str(self.base_dir), backup_path=str(target_dir),
            files_included=len(copied_files), total_bytes=sum(f.stat().st_size for f in copied_files if f.exists()), checksum_manifest=self.build_checksum_manifest(copied_files), status=OpsStatus.PASS
        )
        self.store.append_backup_manifest(manifest)
        return manifest

    def _validate_file_worker(self, path_str: str, expected_hash: str) -> str | None:
        p = Path(path_str)
        if not p.exists():
            return f"Missing file: {p}"
        try:
            with open(p, "rb") as f:
                if hashlib.file_digest(f, "sha256").hexdigest() != expected_hash:
                    return f"Checksum mismatch for {p}"
        except Exception as e:
            return f"Could not read {p}: {e}"
        return None

    def validate_backup(self, manifest: BackupManifest) -> list[str]:
        import concurrent.futures
        errors = []
        bkp_dir = Path(manifest.backup_path)
        if not bkp_dir.exists():
            errors.append(f"Backup path {manifest.backup_path} does not exist.")
            return errors

        # Validate files in parallel since hashing large backup datasets is I/O intensive
        with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
            futures = [
                executor.submit(self._validate_file_worker, path_str, expected_hash)
                for path_str, expected_hash in manifest.checksum_manifest.items()
            ]
            for future in concurrent.futures.as_completed(futures):
                err = future.result()
                if err:
                    errors.append(err)
        return errors
