import pytest
import time
from pathlib import Path
from bist_signal_bot.maintenance.cleanup import CleanupManager
from bist_signal_bot.maintenance.models import RetentionTarget, RetentionPolicy

def test_cleanup_manager_dry_run_analyzes(tmp_path):
    base_dir = tmp_path / "data"
    reports_dir = base_dir / "reports"
    reports_dir.mkdir(parents=True)

    # Create an old file
    old_file = reports_dir / "old_report.json"
    old_file.write_text("old")

    # Set modification time to 200 days ago
    past_time = time.time() - (200 * 24 * 3600)
    import os
    os.utime(old_file, (past_time, past_time))

    manager = CleanupManager(base_dir)
    policy = RetentionPolicy(target=RetentionTarget.REPORTS, keep_days=180, keep_min_count=0)

    result = manager.analyze(policies=[policy])

    assert result.status.value == "SUCCESS"
    assert len(result.candidates) == 1
    assert result.candidates[0].relative_path == "reports/old_report.json"
    assert result.deleted_files == 0 # Dry run

def test_cleanup_manager_requires_confirm(tmp_path):
    manager = CleanupManager(tmp_path)
    result = manager.analyze(targets=[RetentionTarget.REPORTS])

    with pytest.raises(Exception) as excinfo:
        manager.apply_cleanup(result, confirm=False)
    assert "confirm" in str(excinfo.value).lower()

def test_cleanup_manager_safe_to_delete(tmp_path):
    manager = CleanupManager(tmp_path)

    # Research ledger is unsafe by default
    ledger_file = tmp_path / "ledger.jsonl"
    is_safe, warnings = manager.is_safe_to_delete(ledger_file, RetentionTarget.RESEARCH_LEDGER)
    assert not is_safe
    assert any("disabled by default" in w for w in warnings)

    # Secret files are unsafe
    env_file = tmp_path / ".env"
    is_safe, warnings = manager.is_safe_to_delete(env_file, RetentionTarget.TEMP)
    assert not is_safe
    assert any("matching exclude" in w for w in warnings)
