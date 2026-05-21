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
