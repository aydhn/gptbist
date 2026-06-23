import pytest
import os
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.scanner.storage import ScanReportStore
from bist_signal_bot.scanner.models import ScanReport, ScanRequest, ScanUniverseMode, ScanRankingItem, SymbolScanResult, SymbolScanIssue, ScanCandidateStatus

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





def test_scan_report_store_save_csv(tmp_path):
    settings = Settings()
    store = ScanReportStore(settings, base_dir=tmp_path)
    req = ScanRequest(strategy_name="test_strat", universe_mode=ScanUniverseMode.SYMBOLS, symbols=["A", "B", "C"])
    report = ScanReport(request=req)

    # Empty report should create no CSV files
    paths = store.save_csv(report)
    assert not paths

    # Populate report fields
    report.rankings = [
        ScanRankingItem(symbol="A", rank_score=0.9, rank=1, status=ScanCandidateStatus.PASSED),
        ScanRankingItem(symbol="B", rank_score=0.8, rank=2, status=ScanCandidateStatus.PASSED)
    ]
    report.results = [
        SymbolScanResult(symbol="A", status=ScanCandidateStatus.PASSED),
        SymbolScanResult(symbol="B", status=ScanCandidateStatus.PASSED)
    ]
    report.issues = [
        SymbolScanIssue(symbol="C", stage="filter", message="missing data", severity="ERROR")
    ]

    paths = store.save_csv(report)

    assert "rankings" in paths
    assert "results" in paths
    assert "issues" in paths

    assert os.path.exists(paths["rankings"])
    assert os.path.exists(paths["results"])
    assert os.path.exists(paths["issues"])
