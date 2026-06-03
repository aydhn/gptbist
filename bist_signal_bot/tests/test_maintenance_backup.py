import pytest
from pathlib import Path
from bist_signal_bot.maintenance_automation.models import MaintenanceStatus
from bist_signal_bot.maintenance_automation.backup import BackupManifestBuilder

def test_backup_default_paths(tmp_path):
    builder = BackupManifestBuilder(tmp_path)
    paths = builder.default_backup_paths()
    assert len(paths) == 3
    assert any("reports" in str(p) for p in paths)

def test_backup_checksum_manifest(tmp_path):
    builder = BackupManifestBuilder(tmp_path)
    test_file = tmp_path / "test.txt"
    with open(test_file, 'w') as f:
        f.write("hello")

    manifest = builder.build_backup_manifest([test_file], dry_run=True)
    assert len(manifest.checksum_manifest) == 1
    assert str(test_file) in manifest.checksum_manifest
