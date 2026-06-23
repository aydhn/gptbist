import json
import pytest
import os
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.scanner.storage import ScanReportStore
from bist_signal_bot.scanner.models import ScanReport, ScanRequest, ScanUniverseMode, ScanRankingItem, SymbolScanResult, ScanCandidateStatus, SymbolScanIssue, ScanStatus

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


def test_save_csv(tmp_path):
    settings = Settings()
    store = ScanReportStore(settings, base_dir=tmp_path)

    req = ScanRequest(strategy_name="test_csv", universe_mode=ScanUniverseMode.SYMBOLS, symbols=["A", "B"])
    report = ScanReport(request=req)

    # Add mock data
    report.rankings = [
        ScanRankingItem(symbol="A", rank_score=90.0, rank=1, status="PASSED"),
        ScanRankingItem(symbol="B", rank_score=80.0, rank=2, status="PASSED")
    ]
    report.results = [
        SymbolScanResult(symbol="A", status=ScanCandidateStatus.PASSED, rank=1, rank_score=90.0),
        SymbolScanResult(symbol="B", status=ScanCandidateStatus.PASSED, rank=2, rank_score=80.0)
    ]
    report.issues = [
        SymbolScanIssue(stage="TEST", message="Test issue 1", severity="INFO")
    ]

    # Test save_csv with default output_dir
    paths = store.save_csv(report)

    assert "rankings" in paths
    assert "results" in paths
    assert "issues" in paths

    for key, path in paths.items():
        assert path.exists()
        assert path.suffix == ".csv"
        # Verify content briefly
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            assert len(content) > 0
            if key == "rankings":
                assert "symbol" in content
                assert "A" in content
            elif key == "results":
                assert "symbol" in content
                assert "B" in content
            elif key == "issues":
                assert "stage" in content
                assert "TEST" in content

    # Test save_csv with custom output_dir
    custom_dir = tmp_path / "custom_csv_dir"
    custom_dir.mkdir()

    paths_custom = store.save_csv(report, output_dir=custom_dir)
    assert "rankings" in paths_custom
    assert paths_custom["rankings"].parent == custom_dir
    assert paths_custom["rankings"].name == "rankings.csv"

    # Test save_csv with empty data
    empty_report = ScanReport(request=req)
    empty_paths = store.save_csv(empty_report)
    assert len(empty_paths) == 0
