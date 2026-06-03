import pytest
from pathlib import Path
from bist_signal_bot.maintenance_automation.staleness import MaintenanceStalenessDetector

def test_staleness_reports(tmp_path):
    detector = MaintenanceStalenessDetector(tmp_path)
    reports_dir = tmp_path / "data" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    candidates = detector.detect_stale_reports()
    assert len(candidates) == 1
    assert "mock_stale_report.md" in candidates[0].path

def test_staleness_failed_jobs(tmp_path):
    detector = MaintenanceStalenessDetector(tmp_path)
    jobs = detector.detect_failed_recent_jobs()
    assert len(jobs) > 0
