import pytest
from pathlib import Path
from bist_signal_bot.maintenance_automation.models import MaintenanceArtifactKind, CleanupCandidate, MaintenanceStatus
from bist_signal_bot.maintenance_automation.cleanup import MaintenanceCleanupEngine

def test_cleanup_engine_safe_to_delete(tmp_path):
    engine = MaintenanceCleanupEngine(base_dir=tmp_path)
    source_file = tmp_path / "test.py"
    source_file.touch()
    assert not engine.safe_to_delete(source_file, MaintenanceArtifactKind.CUSTOM)

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "settings.json"
    config_file.touch()
    assert not engine.safe_to_delete(config_file, MaintenanceArtifactKind.CUSTOM)

    cache_file = tmp_path / "cache.bin"
    cache_file.touch()
    assert engine.safe_to_delete(cache_file, MaintenanceArtifactKind.CACHE)

def test_cleanup_engine_dry_run_paths(tmp_path):
    engine = MaintenanceCleanupEngine(base_dir=tmp_path)
    candidate = CleanupCandidate(
        candidate_id="1",
        artifact_kind=MaintenanceArtifactKind.CACHE,
        path=str(tmp_path / "cache.bin"),
        reason="test"
    )
    res = engine.cleanup(candidate, dry_run=True, confirm=True)
    assert res.status == MaintenanceStatus.PASS
    assert not res.skipped
    assert len(res.affected_paths) == 1
    assert len(res.deleted_paths) == 0

def test_cleanup_engine_no_confirm(tmp_path):
    engine = MaintenanceCleanupEngine(base_dir=tmp_path)
    candidate = CleanupCandidate(
        candidate_id="1",
        artifact_kind=MaintenanceArtifactKind.CACHE,
        path=str(tmp_path / "cache.bin"),
        reason="test"
    )
    res = engine.cleanup(candidate, dry_run=True, confirm=False)
    assert res.status == MaintenanceStatus.SKIPPED
    assert res.skipped
