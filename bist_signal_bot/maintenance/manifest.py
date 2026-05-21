import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from bist_signal_bot.maintenance.models import (
    BackupManifest,
    BackupRequest,
    BackupFileEntry,
    BackupScope,
    BackupFormat
)
from bist_signal_bot.maintenance.checksum import ChecksumManager
from bist_signal_bot.core.exceptions import BackupManifestError

class BackupManifestBuilder:
    @staticmethod
    def should_exclude(path: Path) -> tuple[bool, str | None]:
        name = path.name.lower()

        # Exact matches
        if name in ['.env', '.gitignore', '.git']:
            return True, f"Excluded by rule: exact match ({name})"

        # Prefixes
        if name.startswith('.env.'):
            return True, "Excluded by rule: .env file"

        # Suffixes
        if name.endswith('.pem') or name.endswith('.key'):
            return True, "Excluded by rule: private key"

        # Substrings
        if 'secret' in name:
            return True, "Excluded by rule: contains 'secret'"
        if 'token' in name:
            return True, "Excluded by rule: contains 'token'"
        if 'credentials' in name:
            return True, "Excluded by rule: contains 'credentials'"

        # Common exclude dirs
        if '__pycache__' in path.parts:
            return True, "Excluded by rule: __pycache__"
        if '.pytest_cache' in path.parts:
            return True, "Excluded by rule: .pytest_cache"

        return False, None

    @staticmethod
    def scan_files_for_scope(base_dir: Path, scopes: list[BackupScope]) -> list[BackupFileEntry]:
        entries = []
        if not base_dir.exists():
            return entries

        for path in base_dir.rglob('*'):
            if not path.is_file():
                continue

            try:
                rel_path = str(path.relative_to(base_dir))
            except ValueError:
                continue

            is_excluded, reason = BackupManifestBuilder.should_exclude(path)

            # Simple scope mapping for MVP
            scope = BackupScope.ALL_SAFE
            if 'market_data' in path.parts:
                scope = BackupScope.MARKET_DATA
            elif 'reports' in path.parts:
                scope = BackupScope.REPORTS

            # If scopes doesn't contain ALL_SAFE, and scope isn't in requested scopes, exclude it
            if BackupScope.ALL_SAFE not in scopes and scope not in scopes:
                is_excluded = True
                reason = f"Excluded by scope rule: file scope {scope.value} not in requested scopes"

            size = path.stat().st_size

            entries.append(BackupFileEntry(
                relative_path=rel_path,
                size_bytes=size,
                scope=scope,
                included=not is_excluded,
                excluded_reason=reason
            ))

        return entries

    @staticmethod
    def build_manifest(request: BackupRequest, base_dir: Path, files: list[BackupFileEntry], archive_path: Path | None = None) -> BackupManifest:
        manifest_id = f"mf_{uuid.uuid4().hex[:12]}"
        backup_id = f"bk_{uuid.uuid4().hex[:12]}"

        included_files = [f for f in files if f.included]
        excluded_files = [f for f in files if not f.included]

        total_size = sum(f.size_bytes for f in included_files)

        archive_path_str = str(archive_path) if archive_path else None
        archive_checksum = ChecksumManager.sha256_file(archive_path) if archive_path and archive_path.exists() else None

        return BackupManifest(
            manifest_id=manifest_id,
            backup_id=backup_id,
            created_at=datetime.now(timezone.utc),
            app_version="1.0.0",
            schema_version="1.0.0",
            backup_format=request.backup_format,
            scopes=request.scopes,
            file_entries=files,
            total_files=len(files),
            included_files=len(included_files),
            excluded_files=len(excluded_files),
            total_size_bytes=total_size,
            archive_path=archive_path_str,
            checksum_sha256=archive_checksum
        )

    @staticmethod
    def write_manifest(manifest: BackupManifest, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / f"{manifest.backup_id}_manifest.json"

        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

        return manifest_path

    @staticmethod
    def load_manifest(path: Path) -> BackupManifest:
        if not path.exists():
            raise BackupManifestError(f"Manifest file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return BackupManifest.model_validate(data)
        except Exception as e:
            raise BackupManifestError(f"Failed to load manifest from {path}: {e}")

    @staticmethod
    def verify_manifest(manifest: BackupManifest, base_dir: Path | None = None, archive_path: Path | None = None) -> list[str]:
        errors = []

        if archive_path and manifest.checksum_sha256:
            if not archive_path.exists():
                errors.append(f"Archive file not found: {archive_path}")
            else:
                try:
                    actual_checksum = ChecksumManager.sha256_file(archive_path)
                    if actual_checksum != manifest.checksum_sha256:
                        errors.append(f"Archive checksum mismatch. Expected {manifest.checksum_sha256}, got {actual_checksum}")
                except ChecksumError as e:
                    errors.append(f"Failed to calculate archive checksum: {e}")

        if base_dir and base_dir.exists():
            for entry in manifest.file_entries:
                if not entry.included:
                    continue

                full_path = base_dir / entry.relative_path
                if not full_path.exists():
                    errors.append(f"File missing from base dir: {entry.relative_path}")
                elif entry.checksum_sha256:
                    try:
                        actual_checksum = ChecksumManager.sha256_file(full_path)
                        if actual_checksum != entry.checksum_sha256:
                            errors.append(f"File checksum mismatch for {entry.relative_path}. Expected {entry.checksum_sha256}, got {actual_checksum}")
                    except ChecksumError as e:
                        errors.append(f"Failed to calculate checksum for {entry.relative_path}: {e}")

        return errors
