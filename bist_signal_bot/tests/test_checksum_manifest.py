import pytest
import json
from datetime import datetime, timezone
from bist_signal_bot.core.exceptions import BackupManifestError
from bist_signal_bot.maintenance.models import BackupFormat, BackupScope
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

def test_load_manifest_success(tmp_path):
    manifest_data = {
        "manifest_id": "mf_123",
        "backup_id": "bk_123",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "app_version": "1.0.0",
        "schema_version": "1.0.0",
        "backup_format": "ZIP",
        "scopes": ["ALL_SAFE"],
        "file_entries": [],
        "total_files": 0,
        "included_files": 0,
        "excluded_files": 0,
        "total_size_bytes": 0,
        "warnings": [],
        "disclaimer": "Backup manifest is operational metadata only. No real order was sent.",
        "metadata": {}
    }

    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(json.dumps(manifest_data))

    manifest = BackupManifestBuilder.load_manifest(manifest_file)
    assert manifest.manifest_id == "mf_123"
    assert manifest.backup_id == "bk_123"
    assert manifest.backup_format == BackupFormat.ZIP
    assert manifest.scopes == [BackupScope.ALL_SAFE]

def test_load_manifest_not_found(tmp_path):
    non_existent_file = tmp_path / "does_not_exist.json"
    with pytest.raises(BackupManifestError, match="Manifest file not found"):
        BackupManifestBuilder.load_manifest(non_existent_file)

def test_load_manifest_invalid_json(tmp_path):
    invalid_json_file = tmp_path / "invalid.json"
    invalid_json_file.write_text("{ invalid json")

    with pytest.raises(BackupManifestError, match="Failed to load manifest"):
        BackupManifestBuilder.load_manifest(invalid_json_file)

def test_load_manifest_schema_validation_error(tmp_path):
    invalid_schema_data = {
        "manifest_id": "mf_123",
        # Missing other required fields
    }
    invalid_schema_file = tmp_path / "invalid_schema.json"
    invalid_schema_file.write_text(json.dumps(invalid_schema_data))

    with pytest.raises(BackupManifestError, match="Failed to load manifest"):
        BackupManifestBuilder.load_manifest(invalid_schema_file)
