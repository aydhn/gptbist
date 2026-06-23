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

def test_save_csv(tmp_path):
    from bist_signal_bot.scanner.models import ScanRankingItem, SymbolScanResult, SymbolScanIssue, ScanCandidateStatus

    settings = Settings()
    store = ScanReportStore(settings, base_dir=tmp_path)
    req = ScanRequest(strategy_name="test_strat_csv", universe_mode=ScanUniverseMode.SYMBOLS, symbols=["A"])
    report = ScanReport(
        request=req,
        rankings=[ScanRankingItem(symbol="A", rank_score=80.0, rank=1, status="PASSED")],
        results=[SymbolScanResult(symbol="A", status=ScanCandidateStatus.PASSED, rank=1, rank_score=80.0)],
        issues=[SymbolScanIssue(symbol="A", stage="Test", message="Some issue")]
    )

    paths = store.save_csv(report)

    assert "rankings" in paths
    assert "results" in paths
    assert "issues" in paths
    assert os.path.exists(paths["rankings"])
    assert os.path.exists(paths["results"])
    assert os.path.exists(paths["issues"])

def test_save_csv_empty(tmp_path):
    from bist_signal_bot.scanner.models import ScanCandidateStatus

    settings = Settings()
    store = ScanReportStore(settings, base_dir=tmp_path)
    req = ScanRequest(strategy_name="test_strat_csv_empty", universe_mode=ScanUniverseMode.SYMBOLS, symbols=["A"])
    report = ScanReport(
        request=req,
        rankings=[],
        results=[],
        issues=[]
    )

    paths = store.save_csv(report)

    assert "rankings" not in paths
    assert "results" not in paths
    assert "issues" not in paths
    assert len(paths) == 0

def test_save_csv_custom_dir(tmp_path):
    from bist_signal_bot.scanner.models import ScanRankingItem

    settings = Settings()
    store = ScanReportStore(settings, base_dir=tmp_path)
    req = ScanRequest(strategy_name="test_strat_csv_custom", universe_mode=ScanUniverseMode.SYMBOLS, symbols=["A"])
    report = ScanReport(
        request=req,
        rankings=[ScanRankingItem(symbol="A", rank_score=80.0, rank=1, status="PASSED")]
    )

    custom_dir = tmp_path / "custom" / "path"
    custom_dir.mkdir(parents=True)
    paths = store.save_csv(report, output_dir=custom_dir)

    assert "rankings" in paths
    assert paths["rankings"].parent == custom_dir
    assert os.path.exists(paths["rankings"])
