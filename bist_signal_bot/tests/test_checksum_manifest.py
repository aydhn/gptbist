from datetime import datetime, timezone
from bist_signal_bot.maintenance.models import BackupManifest, BackupFileEntry, BackupScope, BackupFormat
import pytest
from pathlib import Path
from bist_signal_bot.maintenance.checksum import ChecksumManager
from bist_signal_bot.maintenance.manifest import BackupManifestBuilder

def test_sha256_deterministic(tmp_path):
    f1 = tmp_path / "test1.txt"
    f1.write_text("hello world")

    hash1 = ChecksumManager.sha256_file(f1)
    hash2 = ChecksumManager.sha256_file(f1)

    assert hash1 == hash2
    assert hash1 == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

def test_manifest_builder_excludes_env(tmp_path):
    env_file = tmp_path / ".env"

    is_excluded, reason = BackupManifestBuilder.should_exclude(env_file)
    assert is_excluded
    assert "exact match" in reason

def test_manifest_builder_excludes_secrets(tmp_path):
    secret_file = tmp_path / "my_secret_token.txt"

    is_excluded, reason = BackupManifestBuilder.should_exclude(secret_file)
    assert is_excluded
    assert "contains 'secret'" in reason


def test_verify_manifest_base_dir(tmp_path):
    base_dir = tmp_path / "base"
    base_dir.mkdir()

    file1 = base_dir / "test1.txt"
    file1.write_text("file1")
    hash1 = ChecksumManager.sha256_file(file1)

    file2 = base_dir / "test2.txt"
    file2.write_text("file2")
    hash2 = ChecksumManager.sha256_file(file2)

    manifest = BackupManifest(
        manifest_id="test-mf",
        backup_id="test-bk",
        created_at=datetime.now(timezone.utc),
        app_version="1.0",
        schema_version="1.0",
        backup_format=BackupFormat.MANIFEST_ONLY,
        scopes=[BackupScope.ALL_SAFE],
        file_entries=[
            BackupFileEntry(relative_path="test1.txt", size_bytes=5, checksum_sha256=hash1, scope=BackupScope.ALL_SAFE, included=True),
            BackupFileEntry(relative_path="test2.txt", size_bytes=5, checksum_sha256=hash2, scope=BackupScope.ALL_SAFE, included=True)
        ],
        total_files=2,
        included_files=2,
        excluded_files=0,
        total_size_bytes=10
    )

    # Test valid manifest
    errors = BackupManifestBuilder.verify_manifest(manifest, base_dir=base_dir)
    assert len(errors) == 0

    # Test missing file
    file2.unlink()
    errors = BackupManifestBuilder.verify_manifest(manifest, base_dir=base_dir)
    assert len(errors) == 1
    assert "File missing" in errors[0]

    # Restore file2 but change content
    file2.write_text("file2_changed")
    errors = BackupManifestBuilder.verify_manifest(manifest, base_dir=base_dir)
    assert len(errors) == 1
    assert "checksum mismatch" in errors[0]

def test_verify_manifest_archive(tmp_path):
    archive_path = tmp_path / "archive.zip"
    archive_path.write_bytes(b"dummy archive content")
    archive_hash = ChecksumManager.sha256_file(archive_path)

    manifest = BackupManifest(
        manifest_id="test-mf",
        backup_id="test-bk",
        created_at=datetime.now(timezone.utc),
        app_version="1.0",
        schema_version="1.0",
        backup_format=BackupFormat.ZIP,
        scopes=[BackupScope.ALL_SAFE],
        file_entries=[],
        total_files=0,
        included_files=0,
        excluded_files=0,
        total_size_bytes=0,
        checksum_sha256=archive_hash
    )

    # Test valid archive
    errors = BackupManifestBuilder.verify_manifest(manifest, archive_path=archive_path)
    assert len(errors) == 0

    # Test missing archive
    missing_archive = tmp_path / "missing.zip"
    errors = BackupManifestBuilder.verify_manifest(manifest, archive_path=missing_archive)
    assert len(errors) == 1
    assert "Archive file not found" in errors[0]

    # Test archive checksum mismatch
    archive_path.write_bytes(b"modified content")
    errors = BackupManifestBuilder.verify_manifest(manifest, archive_path=archive_path)
    assert len(errors) == 1
    assert "Archive checksum mismatch" in errors[0]
