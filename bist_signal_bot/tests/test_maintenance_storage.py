import pytest
from bist_signal_bot.maintenance.storage import MaintenanceStore
from bist_signal_bot.maintenance.models import BackupResult, BackupRequest, MaintenanceStatus, BackupManifest, BackupFormat

def test_maintenance_store_save_list(tmp_path):
    store = MaintenanceStore(tmp_path)

    # Create fake BackupResult
    manifest = BackupManifest(
        manifest_id="mf_1", backup_id="bk_1", created_at="2024-01-01T00:00:00Z",
        app_version="1.0", schema_version="1.0", backup_format=BackupFormat.ZIP,
        scopes=[], file_entries=[], total_files=0, included_files=0, excluded_files=0, total_size_bytes=0
    )
    result = BackupResult(
        backup_id="bk_1", request=BackupRequest(), status=MaintenanceStatus.SUCCESS,
        manifest=manifest, elapsed_seconds=1.0
    )

    paths = store.save_backup_result(result)
    assert paths["result"].exists()
    assert paths["manifest"].exists()

    backups = store.list_backups()
    assert len(backups) == 1
    assert backups[0]["backup_id"] == "bk_1"

    ops = store.list_operations()
    assert len(ops) == 1
    assert ops[0]["operation"] == "BACKUP_CREATE"
