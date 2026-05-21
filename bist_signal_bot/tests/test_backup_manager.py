import pytest
from pathlib import Path
import zipfile
from bist_signal_bot.maintenance.backup import BackupManager
from bist_signal_bot.maintenance.models import BackupRequest, BackupScope

def test_backup_manager_dry_run(tmp_path):
    base_dir = tmp_path / "data"
    output_dir = tmp_path / "backups"
    base_dir.mkdir()
    (base_dir / "test.txt").write_text("data")

    manager = BackupManager(base_dir, output_dir)
    req = BackupRequest(dry_run=True, scopes=[BackupScope.ALL_SAFE])

    result = manager.create_backup(req)

    assert result.status.value == "SUCCESS"
    assert result.output_path is None
    assert not output_dir.exists() or len(list(output_dir.iterdir())) == 0

def test_backup_manager_zip_creation(tmp_path):
    base_dir = tmp_path / "data"
    output_dir = tmp_path / "backups"
    base_dir.mkdir()
    (base_dir / "test.txt").write_text("data")

    manager = BackupManager(base_dir, output_dir)
    req = BackupRequest(dry_run=False, scopes=[BackupScope.ALL_SAFE])

    result = manager.create_backup(req)

    assert result.status.value == "SUCCESS"
    assert result.output_path is not None
    assert Path(result.output_path).exists()

    # Verify ZIP contents
    with zipfile.ZipFile(result.output_path, 'r') as zf:
        assert "test.txt" in zf.namelist()

def test_backup_no_absolute_paths(tmp_path):
    base_dir = tmp_path / "data"
    output_dir = tmp_path / "backups"
    base_dir.mkdir()
    (base_dir / "test.txt").write_text("data")

    manager = BackupManager(base_dir, output_dir)
    req = BackupRequest(dry_run=False, scopes=[BackupScope.ALL_SAFE])

    result = manager.create_backup(req)

    with zipfile.ZipFile(result.output_path, 'r') as zf:
        for name in zf.namelist():
            assert not Path(name).is_absolute()
