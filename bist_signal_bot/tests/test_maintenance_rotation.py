import pytest
from pathlib import Path
from bist_signal_bot.maintenance_automation.models import MaintenanceStatus
from bist_signal_bot.maintenance_automation.rotation import ArtifactRotationEngine

def test_rotation_report_dry_run(tmp_path):
    engine = ArtifactRotationEngine(tmp_path)
    res = engine.rotate_reports(dry_run=True, confirm=True)
    assert res.status == MaintenanceStatus.PASS
    assert not res.skipped

def test_rotation_jsonl_no_confirm(tmp_path):
    engine = ArtifactRotationEngine(tmp_path)
    file_path = tmp_path / "test.jsonl"
    res = engine.compact_jsonl_store(file_path, dry_run=True, confirm=False)
    assert res.status == MaintenanceStatus.SKIPPED
    assert res.skipped
