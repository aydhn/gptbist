import pytest
import os
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.scanner.storage import ScanReportStore
from bist_signal_bot.scanner.models import ScanReport, ScanRequest, ScanUniverseMode

def test_scan_report_store_save(tmp_path):
    settings = Settings()
    store = ScanReportStore(settings, base_dir=tmp_path)
    req = ScanRequest(strategy_name="test_strat", universe_mode=ScanUniverseMode.SYMBOLS, symbols=["A"])
    report = ScanReport(request=req)

    paths = store.save_report(report, formats=["json", "csv", "markdown"])

    assert "json" in paths
    assert "markdown" in paths
    assert os.path.exists(paths["json"])
    assert os.path.exists(paths["markdown"])

def test_get_scans_dir(tmp_path):
    settings = Settings()
    store = ScanReportStore(settings, base_dir=tmp_path)

    scans_dir = store.get_scans_dir()

    assert scans_dir == tmp_path
    assert isinstance(scans_dir, type(tmp_path))

def test_create_scan_output_dir(tmp_path):
    settings = Settings()
    store = ScanReportStore(settings, base_dir=tmp_path)
    req = ScanRequest(
        strategy_name="very_long_strategy_name_that_should_be_truncated",
        universe_mode=ScanUniverseMode.SYMBOLS,
        symbols=["A"]
    )
    report = ScanReport(request=req)

    # Store the actual time for assertions
    dt_str = report.started_at.strftime("%Y%m%d")
    expected_scan_id = report.started_at.strftime("%H%M%S_") + req.strategy_name[:10]

    # Call the method being tested
    output_dir = store.create_scan_output_dir(report)

    # Verify the path
    expected_path = tmp_path / dt_str / expected_scan_id
    assert output_dir == expected_path

    # Verify it creates the directory on disk
    assert os.path.exists(output_dir)
    assert os.path.isdir(output_dir)

import json
from bist_signal_bot.scanner.models import ScanStatus

def test_save_json(tmp_path):
    settings = Settings()
    store = ScanReportStore(settings, base_dir=tmp_path)

    req = ScanRequest(strategy_name="test_strat", universe_mode=ScanUniverseMode.SYMBOLS, symbols=["A"])
    report = ScanReport(request=req, status=ScanStatus.SUCCESS, total_symbols=1)

    # Test save_json with default output_dir
    file_path = store.save_json(report)

    assert file_path.exists()
    assert file_path.name == "scan_report.json"

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["request"]["strategy_name"] == "test_strat"
        assert data["status"] == "SUCCESS"
        assert data["total_symbols"] == 1

    # Test save_json with explicit output_dir
    custom_dir = tmp_path / "custom_dir"
    custom_dir.mkdir()

    file_path2 = store.save_json(report, output_dir=custom_dir)
    assert file_path2.exists()
    assert file_path2.parent == custom_dir
    assert file_path2.name == "scan_report.json"
