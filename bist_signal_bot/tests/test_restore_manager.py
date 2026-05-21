import pytest
from pathlib import Path
from bist_signal_bot.maintenance.restore import RestoreManager
from bist_signal_bot.maintenance.backup import BackupManager
from bist_signal_bot.maintenance.models import RestoreRequest, BackupRequest, BackupScope

def test_restore_manager_dry_run_default(tmp_path):
    base_dir = tmp_path / "data"
    backup_dir = tmp_path / "backups"
    restore_dir = tmp_path / "restore"
    base_dir.mkdir()
    (base_dir / "test.txt").write_text("data")

    backup_mgr = BackupManager(base_dir, backup_dir)
    res = backup_mgr.create_backup(BackupRequest(dry_run=False, scopes=[BackupScope.ALL_SAFE]))
    assert res.status.value == "SUCCESS"

    restore_mgr = RestoreManager(base_dir, backup_mgr)
    req = RestoreRequest(backup_path=res.output_path, target_dir=str(restore_dir))

    # default dry_run is True
    result = restore_mgr.restore(req)

    assert result.status.value == "SUCCESS"
    assert result.restored_files == 0
    assert not restore_dir.exists() or len(list(restore_dir.iterdir())) == 0

def test_restore_manager_requires_confirm(tmp_path):
    base_dir = tmp_path / "data"
    backup_dir = tmp_path / "backups"
    restore_dir = tmp_path / "restore"
    base_dir.mkdir()
    (base_dir / "test.txt").write_text("data")

    backup_mgr = BackupManager(base_dir, backup_dir)
    res = backup_mgr.create_backup(BackupRequest(dry_run=False, scopes=[BackupScope.ALL_SAFE]))

    restore_mgr = RestoreManager(base_dir, backup_mgr)
    req = RestoreRequest(backup_path=res.output_path, target_dir=str(restore_dir), dry_run=False)

    result = restore_mgr.restore(req, confirm=False)

    assert result.status.value == "FAILED"
    assert "confirm" in result.errors[0].lower()

def test_restore_manager_blocks_secrets(tmp_path):
    base_dir = tmp_path / "data"
    backup_dir = tmp_path / "backups"
    restore_dir = tmp_path / "restore"
    base_dir.mkdir()
    (base_dir / "test.txt").write_text("data")

    # Fake a backup that somehow has a secret
    backup_mgr = BackupManager(base_dir, backup_dir)
    import zipfile
    backup_dir.mkdir()
    fake_zip = backup_dir / "fake.zip"
    with zipfile.ZipFile(fake_zip, 'w') as zf:
        zf.writestr(".env", "SECRET=123")

    restore_mgr = RestoreManager(base_dir, backup_mgr)
    req = RestoreRequest(backup_path=str(fake_zip), target_dir=str(restore_dir), dry_run=False)

    result = restore_mgr.restore(req, confirm=True)

    assert result.status.value == "PARTIAL_SUCCESS" or result.status.value == "FAILED"
    assert result.restored_files == 0
    assert result.blocked_files == 1
    assert any("Blocked secret" in e for e in result.errors)
