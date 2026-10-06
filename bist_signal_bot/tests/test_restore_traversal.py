import pytest
from pathlib import Path
import os
import tarfile
import zipfile
from bist_signal_bot.maintenance.restore import RestoreManager
from bist_signal_bot.maintenance.backup import BackupManager
from bist_signal_bot.maintenance.models import RestoreRequest, BackupRequest, BackupScope

def create_malicious_tar(path: Path):
    with tarfile.open(path, 'w:gz') as tar:
        # Create a benign file
        benign_path = path.parent / "benign.txt"
        benign_path.write_text("benign")
        tar.add(benign_path, arcname="benign.txt")

        # Add a malicious entry by modifying TarInfo directly
        info = tarfile.TarInfo(name="../malicious.txt")
        content = b"malicious"
        info.size = len(content)
        import io
        tar.addfile(info, io.BytesIO(content))

def test_restore_manager_blocks_tar_traversal(tmp_path):
    base_dir = tmp_path / "data"
    backup_dir = tmp_path / "backups"
    restore_dir = tmp_path / "restore"
    base_dir.mkdir()
    backup_dir.mkdir()

    malicious_tar = backup_dir / "malicious.tar.gz"
    create_malicious_tar(malicious_tar)

    backup_mgr = BackupManager(base_dir, backup_dir)
    restore_mgr = RestoreManager(base_dir, backup_mgr)
    req = RestoreRequest(backup_path=str(malicious_tar), target_dir=str(restore_dir), dry_run=False)

    result = restore_mgr.restore(req, confirm=True)

    # malicious.txt should not exist outside of restore_dir
    assert not (tmp_path / "malicious.txt").exists()
    assert result.blocked_files >= 1
    assert any("Blocked path traversal risk" in e for e in result.errors)
