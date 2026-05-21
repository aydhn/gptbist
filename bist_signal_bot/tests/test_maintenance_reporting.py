import pytest
from bist_signal_bot.maintenance.reporting import format_maintenance_report_markdown
from bist_signal_bot.maintenance.models import BackupResult, BackupRequest, MaintenanceStatus, BackupManifest, BackupFormat

def test_format_maintenance_report_markdown():
    manifest = BackupManifest(
        manifest_id="mf_1", backup_id="bk_1", created_at="2024-01-01T00:00:00Z",
        app_version="1.0", schema_version="1.0", backup_format=BackupFormat.ZIP,
        scopes=[], file_entries=[], total_files=0, included_files=0, excluded_files=0, total_size_bytes=0
    )
    result = BackupResult(
        backup_id="bk_1", request=BackupRequest(), status=MaintenanceStatus.SUCCESS,
        manifest=manifest, elapsed_seconds=1.0, warnings=["Test warning"]
    )

    md = format_maintenance_report_markdown(result)
    assert "Backup Result: SUCCESS" in md
    assert "Test warning" in md
    assert "operational only" in md
